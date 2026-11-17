"""
data_manager class
 - MongoDB storage for assessments.
 -Create, save, load and query assessments.

"""

from datetime import date

from pymongo.errors import PyMongoError

from RecordRepository import MongoRecordRepository, DataAccessError
from AssessmentRecord import AssessmentRecord

class DataManager:
    def __init__(
        self,
        repository: MongoRecordRepository | None = None,
    ) -> None:
        if repository is None:
            try:
                repository = MongoRecordRepository()
            except PyMongoError:
                raise DataAccessError(
                    "Invalid MongoDB connection settings."
                ) from None

        self._repository: MongoRecordRepository = repository

    @property
    def repository(self) -> MongoRecordRepository:
        return self._repository

    def get_db_status(self) -> str:
        return self._repository.get_status()

    def load_records(self) -> list[AssessmentRecord]:
        return self._repository.load_all()

    def save_records(self, records: list[AssessmentRecord]) -> bool:
        """Save supplied records without deleting omitted MongoDB documents."""
        return self._repository.save_all(records)

    def get_record(self, record_id: str) -> AssessmentRecord | None:
        """Read from MongoDB; None means the record does not exist."""
        return self._repository.get_record(record_id)

    def insert_record(self, record: AssessmentRecord) -> bool:
        """Insert a new record without replacing an existing ID."""
        return self._repository.insert_record(record)

    def update_record(self, record: AssessmentRecord) -> bool:
        """Replace an existing saved record."""
        return self._repository.update_record(record)

    def delete_record(self, record_id: str) -> bool:
        return self._repository.delete_record(record_id)

    def close(self) -> None:
        self._repository.close()

    def create_record(
        self,
        records: list[AssessmentRecord],
        product: dict,
        ai_result: dict,
        decision: dict,
    ) -> AssessmentRecord:
        next_number = self._next_record_number(records)
        record_id = f"PRD-{next_number:04d}"

        return AssessmentRecord(
            record_id=record_id,
            product=product,
            ai_assessment=ai_result,
            decision=decision,
        )

    @staticmethod
    def _next_record_number(records: list[AssessmentRecord]) -> int:
        highest_number = len(records)

        for record in records:
            record_id = record.record_id

            if record_id.startswith("PRD-") and record_id[4:].isdigit():
                number = int(record_id[4:])
                highest_number = max(highest_number, number)

        return highest_number + 1

    @staticmethod
    def find_by_id(
        records: list[AssessmentRecord],
        record_id: str,
    ) -> AssessmentRecord | None:
        normalized_id = record_id.strip().upper()

        for record in records:
            if record.record_id.upper() == normalized_id:
                return record

        return None

    @staticmethod
    def filter_near_expiry(
        records: list[AssessmentRecord],
        days: int,
        today: date,
    ) -> list[AssessmentRecord]:
        matches = []

        for record in records:
            days_left = record.product.days_until_expiry(today)

            if 0 <= days_left <= days:
                matches.append(record)

        return matches