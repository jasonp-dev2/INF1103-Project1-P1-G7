from abc import ABC, abstractmethod

from .AssessmentRecord import AssessmentRecord


class RecordRepository(ABC):
    """Define the methods used to save and load assessment records."""

    @abstractmethod
    def get_status(self) -> str:
        """Return ok, missing, corrupt, or unavailable for failed database reads."""

    @abstractmethod
    def load_all(self) -> list[AssessmentRecord]:
        """Load all persisted records as AssessmentRecord domain instances."""

    @abstractmethod
    def save_all(self, records: list[AssessmentRecord]) -> bool:
        """Persist supplied records; True on success, with no deletion guarantee."""

    @abstractmethod
    def get_record(self, record_id: str) -> AssessmentRecord | None:
        """Read one saved assessment, or return None if it is absent."""

    @abstractmethod
    def insert_record(self, record: AssessmentRecord) -> bool:
        """Insert a new record without replacing an existing ID."""

    @abstractmethod
    def update_record(self, record: AssessmentRecord) -> bool:
        """Replace an existing record without creating a missing ID."""

    @abstractmethod
    def delete_record(self, record_id: str) -> bool:
        """Delete an existing assessment."""

    def close(self) -> None:
        """File and in-memory repositories have no connection to close."""
