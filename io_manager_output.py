# Display the details of single product records
def display_record(record):
    print("\n--- Product Record ---")
    print("Record ID     :", record["record_id"])
    print("Product       :", record["product"])
    print("Quantity      :", record["quantity"])
    print("Expiry date   :", record["expiry_date"])
    print("Current price : $" + format(record["current_price"], ".2f"))

# Display all product records in the list
def display_list(records):
    print("\n--- Product List ---")

    # Check if there are no saved product records
    if len(records) == 0:
        print("No product records found.")
        return
    
    # Display each product record
    for record in records:
        display_record(record)

# Displays the final result after the AI response has been processed by the logic manager
def display_result(result):
    print("\n--- Result ---")
    print("Record ID       :", result["record_id"])
    print("Product         :", result["product"])
    print("Quantity        :", result["quantity"])
    print("Expiry date     :", result["expiry_date"])
    # Display price with 2 decimal places
    print("Current price   : $" + format(result["current_price"], ".2f"))
    print("AI risk level   :", result["risk_level"])
    print("AI predicts     :", result["prediction"])
    print("Outcome         :", result["outcome"])
    print("Discount        :", result["discount"])
    print("Waste cost      :", result["waste_cost"])
    print("Reason          :", result["reason"])

    input("\nPress Enter to continue...")
