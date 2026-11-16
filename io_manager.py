from datetime import datetime, date
import json
from classes.Inputhandler import inputHandler
from classes.product import product

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




# ---------------------------------------------------------------------------
# INPUT ENDS HERE
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

def show_message(text: str) -> None:
    print(text)
def show_warning(text: str) -> None:
    print("Warning: " + text)
def wait_for_enter() -> None:
    input("\nPress Enter to continue...")


# ---------------------------------------------------------------------------
# DISPLAY MENU OPTIONS
# ---------------------------------------------------------------------------
def collect_menu_choice() -> str:
    print("\n===== Expiry & Discount Advisor =====")
    print("1. Assess a new product")
    print("2. Show all products")
    print("3. Show products near expiry")
    print("4. View product details")
    print("0. Exit")
    return input("Choose an option: ").strip()

# Return an ID with surrounding spaces removed and letters made uppercase
def collect_record_id() -> str:
    return input(
        "Enter record ID (e.g. PRD-0001): "
    ).strip().upper()

def collect_days_threshold() -> int:
    user_input = input("Show products expiring within how many days? ")
    while not user_input.strip().isdigit():
        print("Please enter a whole number.")
        user_input = input("Show products expiring within how many days? ")
    return int(user_input)


# ---------------------------------------------------------------------------
# STAFF APPROVAL, ALWAYS NEEDED SINCE IS PART OF OUR BUSIENSS RULES
# ---------------------------------------------------------------------------
def collect_staff_approval(decision: dict) -> bool:
    """Ask staff to approve or reject the recommended discount."""
    print("\n--- Staff approval needed ---")
    print("Recommended discount:", str(decision["discount_percent"]) + "%",
          "-> final price $" + format(decision["final_price"], ".2f"))

    answer = input("Approve this discount? (y/n): ").strip().lower()
    while answer != "y" and answer != "n":
        print("Please enter y or n")
        answer = input("Approve this discount? (y/n): ").strip().lower()

    return answer == "y"













# ---------------------------------------------------------------------------
# Displaying records //// STARTING HERE IS THE OUTPUT
# ---------------------------------------------------------------------------

def display_record(record: dict) -> None:
    """Show the details of a single product record."""
    product = record["product"]
    decision = record["decision"]

    print("\n--- Product Record ---")
    print("Record ID       :", record["record_id"])
    print("Product         :", product["product_name"])
    print("Category        :", product["category"])
    print("Quantity        :", product["quantity_in_stock"])
    print("Expiry date     :", product["expiry_date"])
    print("Current price   : $" + format(product["current_price"], ".2f"))
    
    print(f"Discount Percent: {decision['discount_percent']}%")# call keyword to get the value of discount percent
    print(f"Final Price     : ${decision['final_price']:.2f}")# call keyword to get the value of final price

def display_list(records):
    """Display saved assessments in a table sorted by expiry date, earliest first."""
    print("\n--- Product Stock Table ---")

    if len(records) == 0:
        print("No product records found.")
        return

    sorted_records = sorted(
        records,
        key=lambda record: record["product"]["expiry_date"]
    )
    today = date.today()
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

        expiry = date.fromisoformat(product["expiry_date"])

        if expiry < today:
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


def display_result(record: dict) -> None:
    """Show the final processed result of one assessment."""
    product = record["product"]
    ai = record["ai_assessment"]
    decision = record["decision"]

    # Calculate days remaining today, do not overwrite the saved assessment.
    expiry = date.fromisoformat(product["expiry_date"])
    days_remaining = (expiry - date.today()).days

    if days_remaining < 0:
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

    if days_remaining < 0:
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
    if "staff_approved" in record:
        if record["staff_approved"]:
            print("Staff decision  : APPROVED")
        else:
            print("Staff decision  : REJECTED")

    wait_for_enter()
