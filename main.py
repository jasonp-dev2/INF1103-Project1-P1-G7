"""Expiry & Discount Advisor: coordinate four object-oriented managers."""

import logging
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from AIManager.AIManager import AIManager
from classes.IO_Manager import IO_Manager
from classes.logicManagerClass import logicManager
from data_manager.data_manager import DataManager
from data_manager.RecordRepository import DataAccessError, LocalDataMissingError


def setup_logging() -> None:
    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(
        filename="logs/app.log", level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


class ExpiryAdvisorApp:
    """Coordinates managers; managers retain their own individual responsibilities."""

    def __init__(self, io=None, ai=None, logic=None, data=None) -> None:
        self.io = io if io is not None else IO_Manager()
        self.ai = ai if ai is not None else AIManager()
        self.logic = logic if logic is not None else logicManager()
        self.data = data if data is not None else DataManager()
        self.records = []

    def _load(self) -> None:
        try:
            self.records = self.data.load_records()
        except LocalDataMissingError:
            # Only start empty when neither the cloud nor a local file exists.
            self.io.show_warning("No existing local or cloud records. Starting a new local dataset.")
            if not self.data.initialize_local_dataset():
                raise DataAccessError("Could not initialise local storage.")
            self.records = []
        self.logic.load_categories(
            [record.to_dict()["product"] for record in self.records]
        )
        self.logic.load_settings(self.data.load_discount_settings())
        self.io.show_message(f"Loaded {len(self.records)} saved record(s).")
        if self.data.warning:
            self.io.show_warning(self.data.warning)

    def _assess(self, product: dict) -> tuple[dict, dict]:
        today = date.today()
        self.io.show_message("Requesting AI assessment...")
        ai_result = self.ai.assess_product(product, today)
        if ai_result["status"] != self.ai.STATUS_OK:
            self.io.show_warning(
                "AI unavailable: " + ai_result.get("error", "Unknown error")
                + ". Staff review may be required."
            )
        decision = self.logic.evaluate(product, ai_result, today)
        return ai_result, decision

    def _update_categories(self) -> None:
        self.logic.load_categories(
            [record.to_dict()["product"] for record in self.records]
        )

    def assess_new_product(self) -> None:
        product = self.io.collect_product_info()
        self._update_categories()
        self.logic.load_categories(
            [record.to_dict()["product"] for record in self.records] + [product]
        )
        ai_result, decision = self._assess(product)
        record = self.data.create_record(self.records, product, ai_result, decision)
        if decision["needs_staff_approval"]:
            record.set_staff_approved(self.io.collect_staff_approval(decision))
        if self.data.insert_record(record):
            self.records.append(record)
            self.io.show_message(f"Saved as {record.record_id}.")
            if self.data.warning:
                self.io.show_warning(self.data.warning)
        else:
            self.io.show_warning("Could not save the assessment; it was not added.")
        self.io.display_result(record)

    def show_all_products(self) -> None:
        self.io.display_list(self.records)
        self.io.wait_for_enter()

    def show_near_expiry_products(self) -> None:
        days = self.io.collect_days_threshold()
        matches = self.data.filter_near_expiry(self.records, days, date.today())
        self.io.display_list(matches)
        self.io.wait_for_enter()

    def view_saved_assessment(self) -> None:
        record_id = self.io.collect_record_id()
        record = self.data.find_by_id(self.records, record_id)
        if record is None:
            self.io.show_warning(f"No record found with ID: {record_id}")
            return
        self.io.display_result(record)
        self.io.wait_for_enter()

    def update_product_stock(self) -> None:
        record_id = self.io.collect_record_id()
        record = self.data.find_by_id(self.records, record_id)
        if record is None:
            self.io.show_warning(f"No record found with ID: {record_id}")
            return
        product = record.to_dict()["product"]
        self.io.show_message(
            f"Current stock for {product['product_name']}: {product['quantity_in_stock']}"
        )
        quantity = self.io.collect_stock_quantity(allow_zero=True)
        if quantity == product["quantity_in_stock"]:
            self.io.show_message("Stock is unchanged.")
            return
        product["quantity_in_stock"] = quantity

        # Reassess via AI and Logic Manager: never retain a stale prediction or approval.
        self._update_categories()
        ai_result, decision = self._assess(product)
        updated = type(record).from_dict(record.to_dict())
        updated.update_assessment(product, ai_result, decision)
        if decision["needs_staff_approval"]:
            updated.set_staff_approved(self.io.collect_staff_approval(decision))
        if self.data.update_record(updated):
            self.records = [
                updated if item.record_id == record_id else item
                for item in self.records
            ]
            self.io.show_message("Stock and assessment updated.")
            if self.data.warning:
                self.io.show_warning(self.data.warning)
            self.io.display_result(updated)
        else:
            self.io.show_warning("Stock update could not be saved.")

    def configure_discounts(self) -> None:
        """Edit and persist discount ceilings without overriding AI recommendations."""
        while True:
            action = self.io.collect_discount_settings_action()
            if action == "0":
                return
            if action == "1":
                self.io.display_discount_settings(self.logic.get_settings())
                continue

            previous = self.logic.get_settings()
            if action == "2":
                self.logic.set_max_discount(self.io.collect_discount_percent())
            elif action == "3":
                category = self.io.collect_discount_category()
                cap = self.io.collect_discount_percent()
                self.logic.set_category_discount_cap(category, cap)
            elif action == "4":
                category = self.io.collect_discount_category()
                self.logic.remove_category_discount_cap(category)

            if not self.data.save_discount_settings(self.logic.get_settings()):
                self.logic.load_settings(previous)
                self.io.show_warning("Could not save discount settings; changes reverted.")
                continue
            self.io.show_message("Discount limits saved.")
            self.io.display_discount_settings(self.logic.get_settings())
            self.io.show_message(
                "The global maximum also applies. Raise it to 70% or more "
                "if a category should allow 70%."
            )

    def delete_product(self) -> None:
        record_id = self.io.collect_record_id()
        record = self.data.find_by_id(self.records, record_id)
        if record is None:
            self.io.show_warning(f"No record found with ID: {record_id}")
            return
        if not self.io.ask_yes_no(f"Delete record {record_id}? (y/n): "):
            self.io.show_message("Deletion cancelled.")
            return
        if self.data.delete_record(record_id):
            self.records = [
                item for item in self.records if item.record_id != record_id
            ]
            self._update_categories()
            self.io.show_message(f"Deleted record {record_id}.")
            if self.data.warning:
                self.io.show_warning(self.data.warning)
        else:
            self.io.show_warning("Could not save the deletion.")

    def run(self) -> None:
        try:
            self._load()
            if not self.ai.ai_client.is_configured():
                self.io.show_warning("No AI key configured; assessments will use manual review.")
            actions = {
                "1": self.assess_new_product,
                "2": self.show_all_products,
                "3": self.show_near_expiry_products,
                "4": self.view_saved_assessment,
                "5": self.update_product_stock,
                "6": self.delete_product,
                "7": self.configure_discounts,
            }
            while True:
                choice = self.io.collect_menu_choices()
                if choice == "0":
                    break
                actions[choice]()
        except (KeyboardInterrupt, EOFError):
            self.io.show_message("\nInput closed.")
        except DataAccessError as error:
            # Do not treat corrupted persistence as an empty dataset.
            self.io.show_warning(f"Storage error: {error}")
        finally:
            self.data.close()
            self.io.show_message("Goodbye!")


def main() -> None:
    load_dotenv()
    setup_logging()
    ExpiryAdvisorApp().run()


if __name__ == "__main__":
    main()
