"""
RecordRepository class and subclasses

-JSON and MongoDB storage for assessment records.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
import json
import logging
import os
from pathlib import Path

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from .AssessmentRecord import AssessmentRecord


logger = logging.getLogger(__name__)


class DataAccessError(Exception):
    """Storage failed; this must not be treated as an empty dataset."""


class LocalDataMissingError(DataAccessError):
    """No local backup exists and remote records could not be loaded."""


class RecordRepository(ABC):
    @staticmethod
    def _check_saved_record(data: dict) -> None:
        """Check that saved record components are nonempty dictionaries."""
        if not isinstance(data, dict):
            raise ValueError("Saved record must be a dictionary.")

        for name in ("product", "ai_assessment", "decision"):
            component = data.get(name)

            if not isinstance(component, dict) or not component:
                raise ValueError(f"{name} must be a nonempty dictionary.")

    @abstractmethod
    def load_all(self, include_deleted: bool = False) -> list[AssessmentRecord]:
        """Return records; a missing store is empty, unreadable data raises DataAccessError."""

    @abstractmethod
    def save_all(self, records: list[AssessmentRecord]) -> bool:
        """Upsert supplied records. Omission never deletes a record."""

    def close(self) -> None:
        pass


class JsonRecordRepository(RecordRepository):
    """Keep assessment records and their synchronization state in one JSON file."""
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load_snapshot(self) -> dict:
        """Read and validate the full JSON envelope without changing it."""
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON snapshot.")
            if type(data.get("version")) is not int or data["version"] < 0:
                raise ValueError("version must be a nonnegative integer.")
            if type(data.get("sync_pending")) is not bool:
                raise ValueError("sync_pending must be a boolean.")
            if not isinstance(data.get("records"), list):
                raise ValueError("records must be a list.")
            records = []
            for item in data["records"]:
                self._check_saved_record(item)
                records.append(AssessmentRecord.from_dict(item).to_dict())
            ids = [r["record_id"] for r in records]
            if len(ids) != len(set(ids)):
                raise ValueError("Duplicate record IDs.")
            return {"version": data["version"], "sync_pending": data["sync_pending"], "records": records}
        except (OSError, ValueError, KeyError, TypeError):
            raise DataAccessError("Cannot read the local JSON records or sync metadata.") from None

    def _write_snapshot(self, records: list[AssessmentRecord], version: int,
                        sync_pending: bool) -> bool:
        try:
            if type(version) is not int or version < 0 or type(sync_pending) is not bool:
                raise ValueError("Invalid snapshot metadata.")
            documents = [record.to_dict() for record in records]
            if len({item["record_id"] for item in documents}) != len(documents):
                raise ValueError("Duplicate record IDs.")
            data = {"version": version, "sync_pending": sync_pending, "records": documents}
            self.path.parent.mkdir(parents=True, exist_ok=True)
            contents = json.dumps(data, indent=4, allow_nan=False) + "\n"
            self.path.write_text(contents, encoding="utf-8")
            return True
        except (OSError, ValueError, KeyError, TypeError):
            return False

    def load_all(self, include_deleted: bool = False) -> list[AssessmentRecord]:
        if not self.path.exists():
            return []
        snapshot = self.load_snapshot()
        return [AssessmentRecord.from_dict(item) for item in snapshot["records"]
                if include_deleted or not item["isDeleted"]]

    def save_all(self, records: list[AssessmentRecord]) -> bool:
        """Save local edits with an incremented version and pending flag."""
        try:
            snapshot = self.load_snapshot() if self.path.exists() else {
                "version": 0, "sync_pending": False, "records": []}
            by_id = {item["record_id"]: AssessmentRecord.from_dict(item)
                     for item in snapshot["records"]}
            for record in records:
                by_id[record.record_id] = record
            return self._write_snapshot(list(by_id.values()), snapshot["version"] + 1, True)
        except DataAccessError:
            return False

    def replace_from_cloud(self, records: list[AssessmentRecord]) -> bool:
        """Refresh a synced backup; never overwrite pending local changes."""
        snapshot = self.load_snapshot() if self.path.exists() else {
            "version": 0, "sync_pending": False}
        if snapshot["sync_pending"]:
            raise DataAccessError("Pending local records must be synchronized first.")
        return self._write_snapshot(records, snapshot["version"], False)

    def confirm_synced(self, records: list[AssessmentRecord], version: int) -> bool:
        """Clear pending only for the exact local version that was uploaded."""
        snapshot = self.load_snapshot()
        if snapshot["version"] != version or not snapshot["sync_pending"]:
            return False
        return self._write_snapshot(records, version, False)


class MongoRecordRepository(RecordRepository):
    def __init__(self, uri: str | None = None, database_name: str | None = None,
                 collection_name: str | None = None, client=None):
        # Defer URI/DNS connection work until an operation, allowing offline startup.
        self._client = client
        self._owns_client = client is None
        self._uri = uri or os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
        self._database = database_name or os.environ.get("MONGODB_DATABASE", "expiry_advisor")
        self._name = collection_name or os.environ.get("MONGODB_COLLECTION", "assessments")

    def _collection(self):
        if self._client is None:
            self._client = MongoClient(self._uri, serverSelectionTimeoutMS=8000,
                                       connectTimeoutMS=5000, socketTimeoutMS=10000)
        return self._client[self._database][self._name]

    def load_all(self, include_deleted: bool = False) -> list[AssessmentRecord]:
        try:
            query = {} if include_deleted else {"isDeleted": {"$ne": True}}
            records = []
            for document in self._collection().find(query).sort("_id", 1):
                self._check_saved_record(document)
                record = AssessmentRecord.from_dict(document)
                if document.get("_id") != record.record_id:
                    raise ValueError("MongoDB _id must match record_id.")
                records.append(record)
            return records
        except (PyMongoError, ValueError, KeyError, TypeError):
            raise DataAccessError("Cannot read MongoDB assessments.") from None

    def save_all(self, records: list[AssessmentRecord]) -> bool:
        try:
            for record in records:
                document = record.to_dict()
                document["_id"] = document["record_id"]
                result = self._collection().replace_one(
                    {"_id": document["_id"]}, document, upsert=True)
                if not result.acknowledged:
                    return False
            # Even an empty dataset must verify MongoDB is reachable.
            if not records:
                self._collection().find_one({})
            return True
        except PyMongoError as error:
            logger.warning("MongoDB save failed (%s).", type(error).__name__)
            return False
        except (ValueError, KeyError, TypeError) as error:
            logger.warning("Could not prepare MongoDB records (%s).", type(error).__name__)
            return False

    def close(self) -> None:
        if self._owns_client and self._client is not None:
            self._client.close()
