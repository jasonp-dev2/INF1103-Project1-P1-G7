"""
Data_manager class

-saves locally through json file, then sync with MongoDB

"""
from __future__ import annotations

from datetime import date
import json
import os
from pathlib import Path

from .AssessmentRecord import AssessmentRecord
from .RecordRepository import (
    DataAccessError, LocalDataMissingError, RecordRepository, MongoRecordRepository,
    JsonRecordRepository,
)


class DataManager:
    """Coordinate local and cloud storage; run one application instance at a time."""
    def __init__(self, repository: RecordRepository | None = None,
        json_path: str | Path | None = None) -> None:
        default_file = Path(__file__).resolve().parent.parent / "data" / "products.json"
        self._json = JsonRecordRepository(
            json_path or os.environ.get("DATA_FILE", default_file),
        )
        self._settings_path = self._json.path.parent / "discount_settings.json"
        self._repository = repository if repository is not None else MongoRecordRepository()
        self.warning = ""
        self.loaded_from = ""
        self._closed = False

    def load_discount_settings(self) -> dict:
        """Load local settings, distinct from versioned assessment records."""
        if not self._settings_path.exists():
            return {}
        try:
            saved = json.loads(self._settings_path.read_text(encoding="utf-8"))
            if not isinstance(saved, dict):
                raise ValueError("Settings must be a JSON object.")
            return saved
        except (OSError, ValueError) as error:
            raise DataAccessError("Cannot load local discount settings.") from error

    def save_discount_settings(self, settings: dict) -> bool:
        """Save settings with a temporary file so an interruption cannot truncate them."""
        temporary = self._settings_path.with_suffix(".tmp")
        try:
            if not isinstance(settings, dict):
                raise ValueError("Settings must be a dictionary.")
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            contents = json.dumps(settings, indent=2, allow_nan=False) + "\n"
            temporary.write_text(contents, encoding="utf-8")
            os.replace(temporary, self._settings_path)
            return True
        except (OSError, ValueError, TypeError):
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            return False

    @property
    def sync_pending(self) -> bool:
        return self._json.load_snapshot()["sync_pending"] if self._json.path.exists() else False

    @property
    def version(self) -> int:
        return self._json.load_snapshot()["version"] if self._json.path.exists() else 0

    @staticmethod
    def _active(records: list[AssessmentRecord]) -> list[AssessmentRecord]:
        return [record for record in records if not record.is_deleted]

    def _sync_pending(self, snapshot: dict | None = None) -> bool:
        """Upload the pending snapshot, then clear its flag with a normal JSON write."""
        try:
            if snapshot is None:
                snapshot = self._json.load_snapshot()
            if not snapshot["sync_pending"]:
                return True
            records = [AssessmentRecord.from_dict(item) for item in snapshot["records"]]
            if not self._repository.save_all(records):
                raise DataAccessError("MongoDB save failed.")
            cloud = self._repository.load_all(include_deleted=True)
            cloud_by_id = {record.record_id: record.to_dict() for record in cloud}
            for record in records:
                data = record.to_dict()
                if cloud_by_id.get(data["record_id"]) != data:
                    raise DataAccessError("MongoDB did not confirm the local changes.")
            if not self._json.confirm_synced(cloud, snapshot["version"]):
                raise DataAccessError("Cannot confirm the local snapshot as synchronized.")
            self.warning = ""
            return True
        except DataAccessError:
            self.warning = "Saved locally. MongoDB synchronization is pending."
            return False

    def initialize_local_dataset(self) -> bool:
        """Explicitly start fresh offline; never replace an existing backup."""
        if self._json.path.exists():
            raise DataAccessError("A local dataset already exists; it will not be replaced.")
        return self.save_records([])

    def load_records(self) -> list[AssessmentRecord]:
        # Read once for the pending decision and any offline fallback.
        snapshot = self._json.load_snapshot() if self._json.path.exists() else None
        if snapshot is not None and snapshot["sync_pending"]:
            records = [AssessmentRecord.from_dict(item) for item in snapshot["records"]]
            self.loaded_from = "json"
            if self._sync_pending(snapshot):
                records = self._json.load_all(include_deleted=True)
            return self._active(records)
        try:
            records = self._repository.load_all(include_deleted=True)
        except DataAccessError:
            if snapshot is None:
                raise LocalDataMissingError("MongoDB unavailable and no local backup exists.") from None
            records = [AssessmentRecord.from_dict(item) for item in snapshot["records"]]
            self.loaded_from = "json"
            self.warning = "MongoDB unavailable. Loaded the local JSON backup."
            return self._active(records)
        self.loaded_from = "mongodb"
        self.warning = ""
        if not self._json.replace_from_cloud(records):
            raise DataAccessError("Cannot refresh the JSON backup; local storage must be writable.")
        return self._active(records)

    def save_records(self, records: list[AssessmentRecord]) -> bool:
        """True means records and pending metadata were saved together locally."""
        if not self._json.save_all(records):
            self.warning = "Could not save the local JSON records and sync metadata."
            return False
        self._sync_pending()
        return True

    def get_record(self, record_id: str) -> AssessmentRecord | None:
        return self.find_by_id(self.load_records(), record_id)

    def insert_record(self, record: AssessmentRecord) -> bool:
        self.load_records()
        all_records = self._json.load_all(include_deleted=True)
        if self.find_by_id(all_records, record.record_id, include_deleted=True):
            return False
        return self.save_records([record])

    def update_record(self, record: AssessmentRecord) -> bool:
        if self.get_record(record.record_id) is None:
            return False
        return self.save_records([record])

    def delete_record(self, record_id: str) -> bool:
        record = self.get_record(record_id)
        if record is None:
            return False
        record.set_deleted(True)
        return self.save_records([record])

    def create_record(self, records: list[AssessmentRecord], product: dict,
                      ai_result: dict, decision: dict) -> AssessmentRecord:
        # Include tombstones so deleted IDs are never allocated again.
        saved = self._json.load_all(include_deleted=True) if self._json.path.exists() else []
        number = self._next_record_number(records + saved)
        return AssessmentRecord(f"PRD-{number:04d}", product, ai_result, decision)

    @staticmethod
    def _next_record_number(records: list[AssessmentRecord]) -> int:
        maximum = 0
        for record in records:
            record_id = record.record_id
            if record_id.startswith("PRD-") and record_id[4:].isdigit():
                maximum = max(maximum, int(record_id[4:]))
        return maximum + 1

    @staticmethod
    def find_by_id(records: list[AssessmentRecord], record_id: str,
                   include_deleted: bool = False) -> AssessmentRecord | None:
        normalized = record_id.strip().upper()
        for record in records:
            if record.record_id == normalized:
                if include_deleted or not record.is_deleted:
                    return record
        return None

    @staticmethod
    def filter_near_expiry(records: list[AssessmentRecord], days: int,
                           today: date) -> list[AssessmentRecord]:
        matches = []
        for record in records:
            if record.is_deleted:
                continue
            data = record.to_dict()
            try:
                expiry = date.fromisoformat(data["product"]["expiry_date"])
            except (ValueError, TypeError, KeyError):
                continue  # Malformed saved dates must not crash filtering.
            if 0 <= (expiry - today).days <= days:
                matches.append(record)
        return matches

    def close(self) -> None:
        if not self._closed:
            try:
                self._repository.close()
            finally:
                self._closed = True
