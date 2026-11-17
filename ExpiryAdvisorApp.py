"""Coordinate the four managers and run the terminal menu."""

from datetime import date

from AIManager.AIManager import AIManager
from classes.AIAssessment import AIAssessment
from classes.Decision import Decision
from classes.IO_Manager import IO_Manager
from classes.logicManagerClass import logicManager
from data_manager.DataAccessError import DataAccessError
from data_manager.data_manager import DataManager


class ExpiryAdvisorApp:
    def __init__(
        self,
        io_manager: IO_Manager,
        ai_manager: AIManager,
        logic_manager: logicManager,
        data_manager: DataManager,
    ) -> None:
        self._io_manager = io_manager
        self._ai_manager = ai_manager
        self._logic_manager = logic_manager
        self._data_manager = data_manager

    def assess_new_product(self) -> None:
        """Menu option 1: the full pipeline for one product."""
        today = date.today()

        # 1. io_manager: get validated product details from the user
        product = self._io_manager.collect_product_info()
        product_data = product.to_dict()

        # 2. ai_manager: ask the AI for an assessment
        self._io_manager.show_message("Waiting for the AI response...")
        ai_result = self._ai_manager.assess_product(product_data, today)
        if ai_result["status"] != self._ai_manager.STATUS_OK:
            self._io_manager.show_warning("AI assessment unavailable: " + ai_result["error"]
                                    + " The item is sent to manual review.")

        # 3. logic_manager: apply the business rules
        decision = self._logic_manager.evaluate(product_data, ai_result, today)

        record = self._data_manager.create_record(
            self._data_manager.load_records(),
            product,
            AIAssessment.from_dict(ai_result),
            Decision.from_dict(decision),
        )

        if decision["needs_staff_approval"]:
            record.staff_approved = self._io_manager.collect_staff_approval(decision)

        if self._data_manager.insert_record(record):
            self._io_manager.show_message("Saved as " + record.record_id)
        else:
            self._io_manager.show_warning("Could not save the assessment to MongoDB.")

        self._io_manager.display_result(record.to_dict())


    def show_all_products(self) -> None:
        records = self._data_manager.load_records()
        self._io_manager.display_list([record.to_dict() for record in records])
        self._io_manager.wait_for_enter()


    def show_near_expiry_products(self) -> None:
        days = self._io_manager.collect_days_threshold()
        matches = self._data_manager.filter_near_expiry(self._data_manager.load_records(), days, date.today())
        self._io_manager.display_list([record.to_dict() for record in matches])
        self._io_manager.wait_for_enter()


    def view_saved_assessment(self) -> None:
        record_id = self._io_manager.collect_record_id()
        record = self._data_manager.get_record(record_id)
        if record is None:
            self._io_manager.show_message("No record found with ID: " + record_id)
            return

        self._io_manager.show_message("\nShowing the previously recorded assessment.")
        self._io_manager.display_result(record.to_dict())


    def remove_product(self) -> None:
        record_id = self._io_manager.collect_record_id()
        if self._data_manager.get_record(record_id) is None:
            self._io_manager.show_message(f"No record found with ID: {record_id}")
            return

        if not self._io_manager.confirm_delete(record_id):
            self._io_manager.show_message("Deletion cancelled.")
            return

        if self._data_manager.delete_record(record_id):
            self._io_manager.show_message(f"Deleted record {record_id}.")
        else:
            self._io_manager.show_warning("Could not save the deletion.")


    def run(self) -> None:
        try:
            try:
                records = self._data_manager.load_records()
                self._io_manager.show_message(f"Loaded {len(records)} saved record(s).")
            except DataAccessError as error:
                self._io_manager.show_warning(str(error))

            if not self._ai_manager.ai_client.is_configured():
                self._io_manager.show_warning("No API key found. Products will go to manual review.")

            choice = self._io_manager.collect_menu_choices()
            while choice != "0":
                try:
                    if choice == "1":
                        self.assess_new_product()
                    elif choice == "2":
                        self.show_all_products()
                    elif choice == "3":
                        self.show_near_expiry_products()
                    elif choice == "4":
                        self.view_saved_assessment()
                    elif choice == "5":
                        self.remove_product()
                    else:
                        self._io_manager.show_message("Please enter 0, 1, 2, 3, 4 or 5.")
                except DataAccessError as error:
                    self._io_manager.show_warning(str(error))
                choice = self._io_manager.collect_menu_choices()
        except (KeyboardInterrupt, EOFError):
            self._io_manager.show_message("\nInput closed.")
        finally:
            self._data_manager.close()
        self._io_manager.show_message("Goodbye!")
