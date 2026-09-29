def display_record(record):
    print("\n--- Product Record ---")
    print("Record ID     :", record["record_id"])
    print("Product       :", record["product"])
    print("Quantity      :", record["quantity"])
    print("Expiry date   :", record["expiry_date"])
    print("Current price : $" + format(record["current_price"], ".2f"))