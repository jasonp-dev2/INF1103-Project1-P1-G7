"""Offline integration tests for the OOP manager contracts."""
from datetime import date, timedelta

from classes.IO_Manager import IO_Manager
from data_manager.AssessmentRecord import AssessmentRecord
from data_manager.RecordRepository import JsonRecordRepository
from data_manager.data_manager import DataManager


def sample_record(stock=10):
    expiry = (date.today() + timedelta(days=2)).isoformat()
    product = {
        "product_name": "Milk", "category": "Dairy & Eggs",
        "quantity_in_stock": stock, "expiry_date": expiry,
        "current_price": 5.0,
    }
    ai = {
        "status": "ok", "risk_level": "medium",
        "recommended_discount_percent": 20,
        "predicted_unsold_quantity": 3,
    }
    decision = {
        "outcome": "DISCOUNT_RECOMMENDED", "rule": "R6",
        "days_to_expiry": 2, "discount_percent": 20,
        "final_price": 4.0, "waste_cost_if_unsold": 15.0,
        "reason": "Test", "needs_staff_approval": True,
    }
    return AssessmentRecord("PRD-0001", product, ai, decision, staff_approved=True)


def test_io_validation_and_object_display(capsys):
    io = IO_Manager(date(2026, 11, 18))
    assert io.valid_category("99") == "no"
    assert io.valid_category("2") == 2
    assert io.valid_stock("0") == "no"
    assert io.valid_stock("0", allow_zero=True) == 0
    assert io.valid_price("abc") == "no"
    assert io.valid_price("2.50") == 2.5
    assert io.valid_date("2026-02-30", date(2026, 11, 18)) == "no"
    record = sample_record()
    io.display_result(record)
    io.display_list([record])
    output = capsys.readouterr().out
    assert "PRD-0001" in output
    assert "Milk" in output


def test_stock_reassessment_clears_previous_approval():
    record = sample_record()
    changed_product = record.to_dict()["product"]
    changed_product["quantity_in_stock"] = 5
    record.update_assessment(
        changed_product,
        {"status": "failed", "error": "Offline"},
        {"outcome": "MANUAL_REVIEW", "needs_staff_approval": False},
    )
    data = record.to_dict()
    assert data["product"]["quantity_in_stock"] == 5
    assert data["ai_assessment"]["status"] == "failed"
    assert "staff_approved" not in data


def test_json_repository_soft_delete_and_roundtrip(tmp_path):
    repository = JsonRecordRepository(tmp_path / "records.json")
    record = sample_record()
    assert repository.save_all([record])
    records = repository.load_all()
    assert len(records) == 1
    records[0].set_deleted(True)
    assert repository.save_all(records)
    assert repository.load_all() == []
    assert len(repository.load_all(include_deleted=True)) == 1


def test_bad_expiry_does_not_crash_filter():
    record = sample_record()
    data = record.to_dict()
    data["product"]["expiry_date"] = "invalid"
    broken = AssessmentRecord.from_dict(data)
    assert DataManager.filter_near_expiry([broken], 7, date.today()) == []
