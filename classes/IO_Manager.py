from datetime import date, datetime

DATE_FORMAT = "%Y-%m-%d"

CATEGORIES = {
    1: "Dairy & Eggs",
    2: "Bakery",
    3: "Meat & Seafood",
    4: "Fruits & Vegetables",
    5: "Frozen Food",
    6: "Beverages",
    7: "Other",
}


class IO_Manager:
    """Collect validated terminal input and show assessments. No file or API access."""

    def __init__(self, today: date | None = None) -> None:
        self._fixed_date = today

    @staticmethod
    def valid_product_name(product_name: str) -> str | None:
        name = product_name.strip()
        return name if name and not name.isdigit() and len(name) <= 60 else None

    @staticmethod
    def valid_category(category_number: str) -> int | str:
        try:
            number = int(category_number.strip())
        except ValueError:
            return "no"
        return number if number in CATEGORIES else "no"

    @staticmethod
    def valid_stock(quantity: str, allow_zero: bool = False) -> int | str:
        value = quantity.strip()
        if not value.isdecimal():
            return "no"
        number = int(value)
        minimum = 0 if allow_zero else 1
        return number if minimum <= number <= 100000 else "no"

    @staticmethod
    def valid_date(date_str: str, today: date | None = None) -> date | str:
        try:
            expiry = datetime.strptime(date_str.strip(), DATE_FORMAT).date()
        except ValueError:
            return "no"
        current = today if today is not None else date.today()
        days = (expiry - current).days
        return expiry if -365 <= days <= 730 else "no"

    @staticmethod
    def valid_price(value: str) -> float | str:
        try:
            price = float(value.strip())
        except ValueError:
            return "no"
        return round(price, 2) if 0 < price <= 10000 else "no"

    @staticmethod
    def collect_record_id() -> str:
        return input("Enter record ID (e.g. PRD-0001): ").strip().upper()

    def display_info(self, record) -> None:
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
        choice = input("Please enter your choice (0-6): ").strip()
        while choice not in ("0", "1", "2", "3", "4", "5", "6"):
            print("Invalid choice. Please enter 0 to 6.")
            choice = input("Please enter your choice (0-6): ").strip()
        return choice

    def collect_product_info(self) -> dict:
        """Return the schema expected by AIManager, LogicManager and AssessmentRecord."""
        print("\n--- Assess a new product ---")
        name = self.valid_product_name(input("Please enter product name: "))
        while name is None:
            print("Invalid product name (1-60 characters, not just digits).")
            name = self.valid_product_name(input("Please enter product name: "))

        print("Category:")
        for number, category in CATEGORIES.items():
            print(f"{number}. {category}")
        category = self.valid_category(input("Please enter category number (1-7): "))
        while category == "no":
            print("Invalid category number.")
            category = self.valid_category(input("Please enter category number (1-7): "))

        stock = self.collect_stock_quantity(allow_zero=False)
        expiry = self.valid_date(input("Expiry date (YYYY-MM-DD): "), self._today())
        while expiry == "no":
            print("Invalid expiry date or date outside allowed range.")
            expiry = self.valid_date(input("Expiry date (YYYY-MM-DD): "), self._today())

        price = self.valid_price(input("Product price per unit ($): "))
        while price == "no":
            print("Invalid price. Enter a number above 0 and no more than 10000.")
            price = self.valid_price(input("Product price per unit ($): "))

        return {
            "product_name": name,
            "category": CATEGORIES[category],
            "quantity_in_stock": stock,
            "expiry_date": expiry.isoformat(),
            "current_price": price,
        }

    def collect_stock_quantity(self, allow_zero: bool = False) -> int:
        quantity = self.valid_stock(input("Quantity in stock: "), allow_zero)
        while quantity == "no":
            print("Enter a valid whole number (0 is allowed for updates)."
                  if allow_zero else "Enter a whole number from 1 to 100000.")
            quantity = self.valid_stock(input("Quantity in stock: "), allow_zero)
        return quantity

    def collect_days_threshold(self) -> int:
        while True:
            text = input("Show products expiring within how many days (1-365)? ").strip()
            if text.isdecimal() and 1 <= int(text) <= 365:
                return int(text)
            print("Please enter a number from 1 to 365.")

    def collect_staff_approval(self, decision: dict) -> bool:
        self.display_approval_request(decision)
        return self.ask_yes_no("Approve this discount? (y/n): ")

    @staticmethod
    def ask_yes_no(prompt: str) -> bool:
        answer = input(prompt).strip().lower()
        while answer not in ("y", "yes", "n", "no"):
            print("Please answer y or n.")
            answer = input(prompt).strip().lower()
        return answer in ("y", "yes")

    @staticmethod
    def _as_dict(record) -> dict:
        if isinstance(record, dict):
            return record
        return record.to_dict()

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

    def display_record(self, record) -> None:
        """Show the details of a single product record."""
        record = self._as_dict(record)
        product = record["product"]

        print("\n--- Product Record ---")
        print("Record ID       :", record["record_id"])
        print("Product         :", product["product_name"])
        print("Category        :", product["category"])
        print("Quantity        :", product["quantity_in_stock"])
        print("Expiry date     :", product["expiry_date"])
        print("Current price   : $" + format(product["current_price"], ".2f"))

    def display_list(self, records: list) -> None:
        """Display saved assessments in a table sorted by expiry date, earliest first."""
        records = [self._as_dict(item) for item in records]
        records = [item for item in records if not item.get('isDeleted', False)]
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


    def display_result(self, record) -> None:
        """Show the final processed result of one assessment."""
        record = self._as_dict(record)
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
        print("Rule applied    :", decision.get("rule", "N/A"))
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