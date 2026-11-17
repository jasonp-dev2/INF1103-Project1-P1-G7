import logging
import os
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from .AssessmentRecord import AssessmentRecord
from .DataAccessError import DataAccessError
from .RecordRepository import RecordRepository

logger = logging.getLogger(__name__)
FILE_OK = "ok"
FILE_UNAVAILABLE = "unavailable"


class MongoRecordRepository(RecordRepository):
    """Store each assessment as a MongoDB document, keyed by its record ID."""

    def __init__(
        self,
        uri: str | None = None,
        database_name: str | None = None,
        collection_name: str | None = None,
        client: MongoClient | None = None,
    ) -> None:
        self._owns_client = client is None
        if client is None:
            client = MongoClient(
                uri or os.environ.get("MONGODB_URI", "mongodb://localhost:27017"),
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
                socketTimeoutMS=5000,
                timeoutMS=5000,
            )
        self._client: MongoClient = client
        database = database_name or os.environ.get("MONGODB_DATABASE", "expiry_advisor")
        collection = collection_name or os.environ.get("MONGODB_COLLECTION", "assessments")
        self._collection: Collection = self._client[database][collection]

    @staticmethod
    def _restore(document: dict[str, Any]) -> AssessmentRecord:
        """Validate stored shape before calling the domain constructors."""
        for key in ("product", "ai_assessment", "decision"):
            if not isinstance(document.get(key), dict):
                raise ValueError(f"Invalid {key} in saved assessment.")
        record = AssessmentRecord.from_dict(document)
        if document.get("_id") != record.record_id:
            raise ValueError("MongoDB _id must match record_id.")
        return record

    @staticmethod
    def _document(record: AssessmentRecord) -> dict[str, Any]:
        data = record.to_dict()
        data["_id"] = record.record_id
        return data

    @staticmethod
    def _write_failed(error: PyMongoError) -> bool:
        # Exception messages may contain connection details, so log only the type.
        logger.warning("MongoDB write failed (%s).", type(error).__name__)
        return False

    def get_status(self) -> str:
        try:
            self.load_all()
        except DataAccessError:
            return FILE_UNAVAILABLE
        return FILE_OK

    def load_all(self) -> list[AssessmentRecord]:
        try:
            records: list[AssessmentRecord] = []
            for document in self._collection.find({}).sort("_id", 1):
                records.append(self._restore(document))
            return records
        except (PyMongoError, KeyError, ValueError, TypeError, OverflowError):
            raise DataAccessError("Could not read saved assessments from MongoDB.") from None

    def get_record(self, record_id: str) -> AssessmentRecord | None:
        try:
            document = self._collection.find_one({"_id": record_id.strip().upper()})
            if document is None:
                return None
            return self._restore(document)
        except (PyMongoError, KeyError, ValueError, TypeError, OverflowError):
            raise DataAccessError("Could not read the assessment from MongoDB.") from None

    def insert_record(self, record: AssessmentRecord) -> bool:
        try:
            result = self._collection.insert_one(self._document(record))
            return result.acknowledged
        except PyMongoError as error:
            return self._write_failed(error)

    def update_record(self, record: AssessmentRecord) -> bool:
        try:
            result = self._collection.replace_one(
                {"_id": record.record_id}, self._document(record)
            )
            return result.acknowledged and result.matched_count == 1
        except PyMongoError as error:
            return self._write_failed(error)

    def delete_record(self, record_id: str) -> bool:
        try:
            result = self._collection.delete_one({"_id": record_id.strip().upper()})
            return result.acknowledged and result.deleted_count == 1
        except PyMongoError as error:
            return self._write_failed(error)

    def save_all(self, records: list[AssessmentRecord]) -> bool:
        """Upsert supplied records; omission never deletes an existing document."""
        try:
            for record in records:
                result = self._collection.replace_one(
                    {"_id": record.record_id}, self._document(record), upsert=True
                )
                if not result.acknowledged:
                    return False
            return True
        except PyMongoError as error:
            return self._write_failed(error)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
