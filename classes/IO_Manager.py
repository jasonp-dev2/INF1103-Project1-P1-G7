from datetime import date, datetime
from classes.productCatergory import productCategory

DATE_FORMAT = "%Y-%m-%d"

class IO_Manager:
    def __init__(self, today: date | None = None) -> None:
        self._fixed_date = today

    @staticmethod
    def valid_product_name(product_name: str) -> str | None:
        product_name = product_name.strip()
        if not product_name or product_name.isdigit():
            return None
        return product_name

    @staticmethod
    def valid_category(category_number: str) -> int | str:
        try:
            number = int(category_number)
        except ValueError:
            return "no"
        if not 1 <= number <= 7:
            return "no"
        return number

    @staticmethod
    def valid_stock(quantity: str) -> int | str:
        if not quantity.isdecimal():
            return "no"
        try:
            return int(quantity)
        except ValueError:
            return "no"

    @staticmethod
    def valid_date(date_str: str) -> date | str:
        try:
            return datetime.strptime(date_str.strip(), DATE_FORMAT).date()
        except ValueError:
            return "no"

    @staticmethod
    def valid_category(category_number: str) -> float | str:
        if not category_number.isdigit():
                    return "no"
        number = int(category_number)
        return number

    @staticmethod
    def collect_record_id() -> str:
        return input("Please enter the record ID: ")

    def display_info(self, record: dict) -> None:
        self.display_record(record)

    def collect_menu_choices(self) -> str:
        print("\n===== Expiry & Discount Advisor =====")
        print("1. Assess a new product")
        print("2. Show all products")
        print("3. Show products near expiry")
        print("4. View product details")
        print("5. Update product stock")
        print("6. Delete product")
        print("0. Exit")
        return input("Please enter your choice (0-6): ")

    @staticmethod
    def collect_product_info() -> productCategory:
        name_prompt = "Please enter product name: "
        product_name = IO_Manager.valid_product_name(input(name_prompt))
        while product_name is None:
            print("Invalid product name. Please try again.")
            product_name = IO_Manager.valid_product_name(input(name_prompt))

        category_prompt = "Please enter product category number (1-7): "
        category_number = IO_Manager.valid_category(input(category_prompt))
        while category_number == "no":
            print("Invalid category number. Please try again.")
            category_number = IO_Manager.valid_category(input(category_prompt))

        quantity_prompt = "Please enter quantity in stock: "
        quantity = IO_Manager.valid_stock(input(quantity_prompt))
        while quantity == "no":
            print("Invalid quantity. Please try again.")
            quantity = IO_Manager.valid_stock(input(quantity_prompt))

        expiry_prompt = "Please enter expiry date (YYYY-MM-DD): "
        expiry_date = IO_Manager.valid_date(input(expiry_prompt))
        while expiry_date == "no":
            print("Invalid date format. Please try again.")
            expiry_date = IO_Manager.valid_date(input(expiry_prompt))

        price_prompt = "Please enter product price per unit ($): "
        price = IO_Manager.valid_price(input(price_prompt))
        while price == "no":
            print("Invalid price. Please try again.")
            price = IO_Manager.valid_price(input(price_prompt))

        return productCategory(product_name, category_number, quantity, expiry_date, price)

    def _today(self) -> date:
        return self._fixed_date if self._fixed_date is not None else date.today()

    def _parse_expiry(self, value: str) -> date | None:
        """Accept saved dates such as 2026-10-09 and older 2026-10-9."""
        try:
            return datetime.strptime(value, DATE_FORMAT).date()
        except ValueError:
            return None

    def _expiry_sort_key(self, record: dict) -> date:
        expiry = self._parse_expiry(record["product"]["expiry_date"])
        return expiry if expiry is not None else date.max

    def show_message(self, text: str) -> None:
        print(text)

    def show_warning(self, text: str) -> None:
        print("Warning: " + text)

    def display_approval_request(self, decision: dict) -> None:
        """Show the recommendation before InputHandler collects y/n."""
        print("\n--- Staff approval needed ---")
        print(f"Recommended discount: {decision['discount_percent']}%")
        print(f"Proposed price: ${decision['final_price']:.2f}")
        print("Reason:", decision["reason"])

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

    def display_list(self, records: list[dict]) -> None:
        """Display saved assessments in a table sorted by expiry date, earliest first."""
        print("\n--- Product Stock Table ---")

        if len(records) == 0:
            print("No product records found.")
            return

        sorted_records = sorted(
            records,
            key=self._expiry_sort_key
        )
        today = self._today()
        # Column headings
        heading = (
            f"{'ID':<10} "
            f"{'Product':<20} "
            f"{'Qty':>5} "
            f"{'Expiry':<10} "
            f"{'Status today':<13} "
            f"{'Risk':<7} "
            f"{'Unsold':>7} "
            f"{'Discount':>9} "
            f"{'Proposed $':>11} "
            f"{'Approval':<12}"
        )

        print(heading)
        print("-" * len(heading))

        # One row for each product
        for record in sorted_records:
            product = record["product"]
            ai = record["ai_assessment"]
            decision = record["decision"]

            expiry = self._parse_expiry(product["expiry_date"])

            if expiry is None:
                expiry_status = "Invalid date"
            elif expiry < today:
                expiry_status = "EXPIRED"
            elif expiry == today:
                expiry_status = "Expires today"
            else:
                expiry_status = "Unexpired"

            if ai["status"] == "ok":
                risk = ai["risk_level"]
                unsold = str(ai["predicted_unsold_quantity"])
            else:
                risk = "N/A"
                unsold = "N/A"

            if decision["needs_staff_approval"]:
                approved = record.get("staff_approved")

                if approved is True:
                    approval = "Approved"
                elif approved is False:
                    approval = "Rejected"
                else:
                    approval = "Pending"
            else:
                approval = "Not required"

            discount = str(decision["discount_percent"]) + "%"
            proposed_price = format(decision["final_price"], ".2f")

            print(
                f"{record['record_id']:<10} "
                f"{product['product_name'][:20]:<20} "
                f"{product['quantity_in_stock']:>5} "
                f"{product['expiry_date']:<10} "
                f"{expiry_status:<13} "
                f"{risk:<7} "
                f"{unsold:>7} "
                f"{discount:>9} "
                f"{proposed_price:>11} "
                f"{approval:<12}"
            )

        print("\nTotal records:", len(records))
        print("Proposed prices are recommendations subject to approval.")
        print("Expired products must not be sold, even if previously approved.")


    def display_result(self, record: dict) -> None:
        """Show the final processed result of one assessment."""
        product = record["product"]
        ai = record["ai_assessment"]
        decision = record["decision"]

        # Calculate days remaining today, do not overwrite the saved assessment.
        expiry = self._parse_expiry(product["expiry_date"])
        days_remaining = None if expiry is None else (expiry - self._today()).days

        if days_remaining is None:
            expiry_status = "Invalid saved date - check the record"
        elif days_remaining < 0:
            expiry_status = f"Expired {abs(days_remaining)} day(s) ago"
        elif days_remaining == 0:
            expiry_status = "Expires today"
        else:
            expiry_status = f"{days_remaining} day(s) remaining"

        print("\n--- Result ---")

        # Product information
        print("Record ID       :", record["record_id"])
        print("Product         :", product["product_name"],
              "(" + product["category"] + ")")
        print("Quantity        :", product["quantity_in_stock"])
        print("Expiry date     :", product["expiry_date"])
        print("Expiry today    :", expiry_status)

        if days_remaining is not None and days_remaining < 0:
            print("*** EXPIRED - DO NOT SELL ***")
            print("Previous approval does not apply to an expired product.")
        print("\n--- Saved assessment ---")
        print("Days left when assessed:", decision["days_to_expiry"])
        print("Current price   : $" + format(product["current_price"], ".2f"))

        # AI assessment (a failed AI result has no risk level or prediction)
        if ai["status"] == "ok":
            print("AI risk level   :", ai["risk_level"])
            print("AI predicts     : about",
                  ai["predicted_unsold_quantity"],
                  "unit(s) unsold")
        else:
            print("AI assessment   : unavailable")

        # Final decision from logic_manager
        print("Saved outcome         :", decision["outcome"])
        print("Rule applied    :", decision["rule"])
        print("Saved discount  :",
              str(decision["discount_percent"]) + "%",
              "-> proposed price $" + format(decision["final_price"], ".2f"))
        print("Waste cost if unsold: $" + format(decision["waste_cost_if_unsold"], ".2f"))
        print("Reason          :", decision["reason"])

        if decision["needs_staff_approval"]:
            print("Staff approval  : REQUIRED")
        else:
            print("Staff approval  : NOT REQUIRED")

        # Only exists if staff were asked
        if decision["needs_staff_approval"]:
            approved = record.get("staff_approved")
            status = "APPROVED" if approved is True else "REJECTED" if approved is False else "PENDING"
            print("Staff decision  :", status)