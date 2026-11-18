"""Offline tests for missing and corrupt persistence failure handling."""
import json
import pytest

from data_manager.AssessmentRecord import AssessmentRecord
from data_manager.RecordRepository import (
    DataAccessError,
    JsonRecordRepository,
    LocalDataMissingError,
    RecordRepository,
)
from data_manager.data_manager import DataManager


class FailingRemoteRepository(RecordRepository):
    """Stub remote repository simulating MongoDB connection failure."""

    def load_all(self, include_deleted: bool = False) -> list[AssessmentRecord]:
        raise DataAccessError("Simulated MongoDB outage.")

    def save_all(self, records: list[AssessmentRecord]) -> bool:
        return False


def _sample_record(record_id="PRD-0001") -> AssessmentRecord:
    return AssessmentRecord(
        record_id=record_id,
        product={
            "product_name": "Bread",
            "category": "Bakery",
            "quantity_in_stock": 8,
            "expiry_date": "2026-11-20",
            "current_price": 3.0,
        },
        ai_assessment={
            "status": "ok",
            "risk_level": "medium",
            "recommended_discount_percent": 20,
            "predicted_unsold_quantity": 2,
        },
        decision={
            "outcome": "DISCOUNT_RECOMMENDED",
            "rule": "R6",
            "reason": "Near expiry",
            "days_to_expiry": 2,
            "discount_percent": 20,
            "final_price": 2.4,
            "waste_cost_if_unsold": 6.0,
            "needs_staff_approval": True,
        },
    )


def test_corrupt_json_file_raises_data_access_error(tmp_path):
    path = tmp_path / "records.json"
    path.write_text("{not valid json", encoding="utf-8")
    repo = JsonRecordRepository(path)
    with pytest.raises(DataAccessError):
        repo.load_all()


def test_invalid_snapshot_schema_or_duplicate_ids_raises_data_access_error(tmp_path):
    path = tmp_path / "records.json"
    path.write_text(json.dumps({"version": -1, "sync_pending": False, "records": []}), encoding="utf-8")
    repo = JsonRecordRepository(path)
    with pytest.raises(DataAccessError):
        repo.load_all()

    dup = _sample_record("PRD-0001").to_dict()
    path.write_text(
        json.dumps({"version": 1, "sync_pending": False, "records": [dup, dup]}),
        encoding="utf-8",
    )
    with pytest.raises(DataAccessError):
        repo.load_all()


def test_missing_local_and_remote_raises_local_data_missing_error(tmp_path):
    data = DataManager(
        repository=FailingRemoteRepository(),
        json_path=tmp_path / "missing.json",
    )
    with pytest.raises(LocalDataMissingError):
        data.load_records()
    data.close()


def test_remote_failure_falls_back_to_local_json_backup(tmp_path):
    json_path = tmp_path / "records.json"
    JsonRecordRepository(json_path).save_all([_sample_record()])

    data = DataManager(
        repository=FailingRemoteRepository(),
        json_path=json_path,
    )
    loaded = data.load_records()
    assert len(loaded) == 1
    assert loaded[0].record_id == "PRD-0001"
    assert data.loaded_from == "json"
    data.close()


def test_corrupt_discount_settings_raises_data_access_error(tmp_path):
    json_path = tmp_path / "records.json"
    settings_path = tmp_path / "discount_settings.json"
    settings_path.write_text("{corrupt", encoding="utf-8")

    data = DataManager(
        repository=FailingRemoteRepository(),
        json_path=json_path,
    )
    with pytest.raises(DataAccessError):
        data.load_discount_settings()
    data.close()
