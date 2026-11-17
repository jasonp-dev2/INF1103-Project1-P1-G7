"""
main.py 
io_manager -> ai_manager -> logic_manager -> data_manager -> io_manager
"""

import logging
import os
from datetime import date

from dotenv import load_dotenv

from AIManager.AIManager import AIManager
from classes.AIAssessment import AIAssessment
from classes.Decision import Decision
from classes.IO_Manager import IO_Manager
from classes.logicManagerClass import logicManager
from data_manager.DataAccessError import DataAccessError
from data_manager.data_manager import DataManager

io_manager = IO_Manager()
logic_manager = logicManager()

def setup_logging() -> None:
    """Send diagnostic messages (e.g. AI failures) to logs/app.log."""
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename="logs/app.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def assess_new_product(data_manager: DataManager, ai_manager: AIManager) -> None:
    """Menu option 1: the full pipeline for one product."""
    today = date.today()

    # 1. io_manager: get validated product details from the user
    product = io_manager.collect_product_info()
    product_data = product.to_dict()

    # 2. ai_manager: ask the AI for an assessment
    io_manager.show_message("Waiting for the AI response...")
    ai_result = ai_manager.assess_product(product_data, today)
    if ai_result["status"] != ai_manager.STATUS_OK:
        io_manager.show_warning("AI assessment unavailable: " + ai_result["error"]
                                + " The item is sent to manual review.")

    # 3. logic_manager: apply the business rules
    decision = logic_manager.evaluate(product_data, ai_result, today)

    record = data_manager.create_record(
        data_manager.load_records(),
        product,
        AIAssessment.from_dict(ai_result),
        Decision.from_dict(decision),
    )

    if decision["needs_staff_approval"]:
        record.staff_approved = io_manager.collect_staff_approval(decision)

    if data_manager.insert_record(record):
        io_manager.show_message("Saved as " + record.record_id)
    else:
        io_manager.show_warning("Could not save the assessment to MongoDB.")

    io_manager.display_result(record.to_dict())


def show_all_products(data_manager: DataManager) -> None:
    records = data_manager.load_records()
    io_manager.display_list([record.to_dict() for record in records])
    io_manager.wait_for_enter()


def show_near_expiry_products(data_manager: DataManager) -> None:
    days = io_manager.collect_days_threshold()
    matches = data_manager.filter_near_expiry(data_manager.load_records(), days, date.today())
    io_manager.display_list([record.to_dict() for record in matches])
    io_manager.wait_for_enter()


def view_saved_assessment(data_manager: DataManager) -> None:
    record_id = io_manager.collect_record_id()
    record = data_manager.get_record(record_id)
    if record is None:
        io_manager.show_message("No record found with ID: " + record_id)
        return

    io_manager.show_message("\nShowing the previously recorded assessment.")
    io_manager.display_result(record.to_dict())


def remove_product(data_manager: DataManager) -> None:
    record_id = io_manager.collect_record_id()
    if data_manager.get_record(record_id) is None:
        io_manager.show_message(f"No record found with ID: {record_id}")
        return

    if not io_manager.confirm_delete(record_id):
        io_manager.show_message("Deletion cancelled.")
        return

    if data_manager.delete_record(record_id):
        io_manager.show_message(f"Deleted record {record_id}.")
    else:
        io_manager.show_warning("Could not save the deletion.")


def run() -> None:
    load_dotenv()
    setup_logging()

    ai_manager = AIManager()
    try:
        data_manager = DataManager()
    except DataAccessError as error:
        io_manager.show_warning(str(error))
        return

    try:
        try:
            records = data_manager.load_records()
            io_manager.show_message(f"Loaded {len(records)} saved record(s).")
        except DataAccessError as error:
            io_manager.show_warning(str(error))

        if not ai_manager.ai_client.is_configured():
            io_manager.show_warning("No API key found. Products will go to manual review.")

        choice = io_manager.collect_menu_choices()
        while choice != "0":
            try:
                if choice == "1":
                    assess_new_product(data_manager, ai_manager)
                elif choice == "2":
                    show_all_products(data_manager)
                elif choice == "3":
                    show_near_expiry_products(data_manager)
                elif choice == "4":
                    view_saved_assessment(data_manager)
                elif choice == "5":
                    remove_product(data_manager)
                else:
                    io_manager.show_message("Please enter 0, 1, 2, 3, 4 or 5.")
            except DataAccessError as error:
                io_manager.show_warning(str(error))
            choice = io_manager.collect_menu_choices()
    except (KeyboardInterrupt, EOFError):
        io_manager.show_message("\nInput closed.")
    finally:
        data_manager.close()
    io_manager.show_message("Goodbye!")


if __name__ == "__main__":
    run()