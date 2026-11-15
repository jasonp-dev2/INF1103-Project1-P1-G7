"""Display product assessments in the terminal."""
from datetime import date, datetime


class OutputHandler:
    """Display the records to staff"""

    def show_message(self, text: str) -> None:
        print(text)

    def show_warning(self, text: str) -> None:
        print("Warning: " + text)

    def wait_for_enter(self) -> None:
        """Pause after a display when the caller asks for it."""
        input("\nPress Enter to continue...")

    def display_record(self, record: dict) -> None:
        """Show the details of a single product record."""
        product = record["product"]

        print("\n--- Product Record ---")
        print("Record ID       :", record["record_id"])
        print("Product         :", product["product_name"])
        print("Category        :", product["category"])
        print("Quantity        :", product["quantity_in_stock"])
        print("Expiry date     :", product["expiry_date"])
        print("Current price   : $" + format(product["current_price"], ".2f"))