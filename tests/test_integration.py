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


class FakeRemoteRepository:
    """In-memory repository used to exercise DataManager without MongoDB."""

    def __init__(self):
        self.records = {}

    def load_all(self, include_deleted=False):
        records = [AssessmentRecord.from_dict(data) for data in self.records.values()]
        return records if include_deleted else [r for r in records if not r.is_deleted]

    def save_all(self, records):
        for record in records:
            self.records[record.record_id] = record.to_dict()
        return True

    def close(self):
        pass


class FakeAI:
    STATUS_OK = "ok"

    class Client:
        def is_configured(self):
            return True

    def __init__(self):
        self.ai_client = self.Client()
        self.calls = 0

    def assess_product(self, product, today):
        self.calls += 1
        return {
            "status": "ok",
            "risk_level": "high",
            "recommended_discount_percent": 30,
            "predicted_unsold_quantity": min(5, product["quantity_in_stock"]),
        }


class FakeIO:
    def __init__(self):
        self.messages = []
        self.output = None

    def collect_product_info(self):
        return sample_record().to_dict()["product"]

    def collect_staff_approval(self, decision):
        return True

    def collect_record_id(self):
        return "PRD-0001"

    def collect_stock_quantity(self, allow_zero=False):
        assert allow_zero
        return 0

    def ask_yes_no(self, prompt):
        return True

    def show_message(self, message):
        self.messages.append(message)

    def show_warning(self, message):
        self.messages.append(message)

    def display_result(self, record):
        self.output = record.to_dict()

    def display_list(self, records):
        pass


def test_full_offline_create_update_delete_flow(tmp_path):
    from classes.logicManagerClass import logicManager
    from main import ExpiryAdvisorApp

    data = DataManager(
        repository=FakeRemoteRepository(),
        json_path=tmp_path / "records.json",
    )
    io = FakeIO()
    ai = FakeAI()
    app = ExpiryAdvisorApp(io=io, ai=ai, logic=logicManager(), data=data)

    app._load()
    assert app.records == []
    app.assess_new_product()
    assert len(app.records) == 1
    assert app.records[0].record_id == "PRD-0001"

    app.update_product_stock()
    assert app.records[0].to_dict()["product"]["quantity_in_stock"] == 0
    assert ai.calls == 2

    app.delete_product()
    assert app.records == []
    assert len(data._json.load_all(include_deleted=True)) == 1
    assert data._json.load_all(include_deleted=True)[0].is_deleted
    data.close()


def test_discount_settings_persist_across_manager_instances(tmp_path):
    from classes.logicManagerClass import logicManager
    file = tmp_path / "products.json"
    data = DataManager(repository=FakeRemoteRepository(), json_path=file)
    logic = logicManager()
    logic.set_max_discount(80)
    logic.set_category_discount_cap("Meat & Seafood", 70)
    assert data.save_discount_settings(logic.get_settings())
    new_data = DataManager(repository=FakeRemoteRepository(), json_path=file)
    restored = logicManager()
    restored.load_settings(new_data.load_discount_settings())
    assert restored.get_final_discount({
        "category": "Meat & Seafood"
    }, 85) == 70
    assert restored.get_final_discount({
        "category": "Meat & Seafood"
    }, 20) == 20
    assert (tmp_path / "discount_settings.json").exists()
    data.close()
    new_data.close()


def test_discount_config_cli_saves_setting(tmp_path):
    from classes.logicManagerClass import logicManager
    from main import ExpiryAdvisorApp

    class SettingsIO(FakeIO):
        def __init__(self):
            super().__init__()
            self.choices = iter(("2", "3", "0"))
            self.percentages = iter((80, 70))

        def collect_discount_settings_action(self):
            return next(self.choices)

        def collect_discount_percent(self):
            return next(self.percentages)

        def collect_discount_category(self):
            return "Meat & Seafood"

        def display_discount_settings(self, settings):
            self.output = settings

    storage = DataManager(
        repository=FakeRemoteRepository(),
        json_path=tmp_path / "records.json",
    )
    app = ExpiryAdvisorApp(
        io=SettingsIO(), ai=FakeAI(), logic=logicManager(), data=storage
    )
    app.configure_discounts()
    assert storage.load_discount_settings()["max_discount"] == 80
    assert app.logic.get_final_discount({"category": "Meat & Seafood"}, 85) == 70
    storage.close()
