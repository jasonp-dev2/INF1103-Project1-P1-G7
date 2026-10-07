# Displays the details of a single product record
def display_record(record):
    product = record["product"]

    print("\n--- Product Record ---")
    print("Record ID     :", record["record_id"])
    print("Product       :", product["product_name"])
    print("Category      :", product["category"])
    print("Quantity      :", product["quantity_in_stock"])
    print("Expiry date   :", product["expiry_date"])
    print("Current price : $" + format(product["current_price"], ".2f"))


# Displays all product records
def display_list(records):
    print("\n--- Product List ---")

    # Check if there are no product records
    if len(records) == 0:
        print("No product records found.")
        return

    # Sort records from closest expiry date to latest expiry date
    sorted_records = sorted(
        records,
        key=lambda record: record["product"]["expiry_date"]
    )

    # Display the sorted product records
    for record in sorted_records:
        display_record(record)


# Displays the final processed result
def display_result(record):
    product = record["product"]
    ai = record["ai_assessment"]
    decision = record["decision"]

    print("\n--- Result ---")
    print("Record ID       :", record["record_id"])
    print("Product         :", product["product_name"],
          "(" + product["category"] + ")")
    print("Quantity        :", product["quantity_in_stock"])
    print("Expiry date     :", product["expiry_date"],
          "(" + str(decision["days_to_expiry"]) + " day(s) left)")
    print("Current price   : $" + format(product["current_price"], ".2f"))
    print("AI risk level   :", ai["risk_level"])
    print("AI predicts     : about",
          ai["predicted_unsold_quantity"], "unit(s) unsold")
    print("Outcome         :", decision["outcome"])
    print("Discount        :", str(decision["discount_percent"]) + "%",
          "-> final price $" + format(decision["final_price"], ".2f"))
    print("Waste cost if unsold: $" +
          format(decision["waste_cost_if_unsold"], ".2f"))
    print("Reason          :", decision["reason"])

    input("\nPress Enter to continue...")
