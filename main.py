"""
main.py 
io_manager -> ai_manager -> logic_manager -> data_manager -> io_manager
"""

import logging
import os
from datetime import date

from dotenv import load_dotenv

import ai_manager
import data_manager
import io_manager
import logic_manager


def setup_logging() -> None:
    """Send diagnostic messages (e.g. AI failures) to logs/app.log."""
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename="logs/app.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def assess_new_product(records: list) -> None:
    """Menu option 1: the full pipeline for one product."""
    today = date.today()

    # 1. io_manager: get validated product details from the user
    product = io_manager.get_product_info()

    # 2. ai_manager: ask the AI for an assessment
    io_manager.show_message("Waiting for the AI response...")
    ai_result = ai_manager.assess_product(product, today)
    if ai_result["status"] != ai_manager.STATUS_OK:
        io_manager.show_warning("AI assessment unavailable: " + ai_result["error"]
                                + " The item is sent to manual review.")

    # 3. logic_manager: apply the business rules
    decision = logic_manager.evaluate(product, ai_result, today)

    # 4. data_manager: combine everything into one record
    record = data_manager.create_record(records, product, ai_result, decision)

    # 5. io_manager: staff must approve any recommended discount
    if decision["needs_staff_approval"]:
        record["staff_approved"] = io_manager.collect_staff_approval(decision)

    # 6. data_manager: save
    records.append(record)
    if data_manager.save_records(records):
        io_manager.show_message("Saved as " + record["record_id"])
    else:
        io_manager.show_warning("Could not save to the data file. "
                                "The record is kept for this session only.")

    # 7. io_manager: show the result
    io_manager.display_result(record)


def show_all_products(records: list) -> None:
    """Menu option 2: show every saved record."""
    io_manager.display_list(records)
    io_manager.wait_for_enter()


def show_near_expiry_products(records: list) -> None:
    """Menu option 3: show records expiring within a number of days."""
    days = io_manager.collect_days_threshold()
    matches = data_manager.filter_near_expiry(records, days, date.today())
    io_manager.display_list(matches)
    io_manager.wait_for_enter()

def view_saved_assessment(records: list) -> None:
    """Menu option 4: display one saved assessment."""
    if not records:
        io_manager.show_message("No saved assessments found.")
        return

    record_id = io_manager.collect_record_id()

    for record in records:
        if record["record_id"].upper() == record_id:
            io_manager.show_message(
                "\nShowing the previously recorded assessment."
            )
            io_manager.display_result(record)
            return

    io_manager.show_message(
        "No record found with ID: " + record_id
    )

def run() -> None:
    load_dotenv()      # reads the API key from the .env file
    setup_logging()

    # data_manager copes with a missing or damaged file; we just tell the user
    if data_manager.get_file_status() == data_manager.FILE_CORRUPT:
        io_manager.show_warning("The saved data file was damaged. It was backed up "
                                "and a new file will be started.")
    records = data_manager.load_records()

    io_manager.show_message("Loaded " + str(len(records)) + " saved record(s).")
    if not ai_manager.is_configured():
        io_manager.show_warning("No API key found. Products will go to manual review.")

    # try/except: Ctrl+C (or closed input) ends the program cleanly
    try:
        choice = io_manager.collect_menu_choice()
        while choice != "0":
            if choice == "1":
                assess_new_product(records)
            elif choice == "2":
                show_all_products(records)
            elif choice == "3":
                show_near_expiry_products(records)
            elif choice == "4":
                view_saved_assessment(records)
            else:
                io_manager.show_message("Please enter 0, 1, 2, 3 or 4.")
            choice = io_manager.collect_menu_choice()
    except (KeyboardInterrupt, EOFError):
        io_manager.show_message("\nInput closed.")
    io_manager.show_message("Goodbye!")


if __name__ == "__main__":
    run()