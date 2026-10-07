"""
data_manager.py - Data layer (saving and loading records).
"""
import json
import os
from datetime import date
from pathlib import Path

DEFAULT_DATA_FILE = "data/products.json"

"""Return the path of the data file as a Path object"""
def get_data_file() -> Path:
    #to check for environemntal variable DATA_FILE, else use default path
    #DATA_FILE is used for testing purposes, avoiding overwrite of data file
    file_path_string = os.environ.get("DATA_FILE", DEFAULT_DATA_FILE)
    return Path(file_path_string)


"""Load all saved records from file as list, return [] if file is missing."""
def load_records() -> list:
    path = get_data_file()
    
    try:
        # Path objects can be passed directly into the open() function
        with path.open("r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

#Save all records directly to the data file.
def save_records(records: list) -> bool: 
    path = get_data_file()
    
    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as file:
            json.dump(records, file, indent=2)
        return True
    except OSError:
        return False

# Create a record using product from io_manager.py, ai_result from ai_manager.py, and decision from decision_manager.py
def create_record(records: list, product: dict, ai_result: dict, decision: dict) -> dict:
    #simple id gen combined with soft deletion flag
    new_id = f"PRD-{len(records) + 1:04d}" #id example PRD-0001
    
    return {
        "record_id": new_id,
        "product": product, 
        "ai_assessment": ai_result,
        "decision": decision,
        "is_deleted": False #for future use in case of CRUD implemenation of soft deletion
    }

#sample filtering function
def filter_near_expiry(records: list, days: int, today: date) -> list:
    #Return records whose product expires within 'days' from today.
    matches = []
    for record in records:
        expiry = date.fromisoformat(record["product"]["expiry_date"])
        days_left = (expiry - today).days
        if 0 <= days_left <= days:
            matches.append(record)
    return matches

#sample filtering function for products near/past expiry, sorting days to expiry in ascending order including expired products (negative)
def filter_and_sort_near_expiry(records: list, today: date, threshold_days: int = 30) -> list[dict]: #threshold days default of 30 days, user definable
    matches = []
    
    for record in records:
        #only selects non-deleted records
        if record.get("is_deleted", False):
            continue

        expiry = date.fromisoformat(record["product"]["expiry_date"])
        days_left = (expiry - today).days

        # adds all records <30 days to expiry or already expired
        if days_left < threshold_days:
            matches.append({
                "record": record,
                "days_left": days_left
            })
            
    #sort numbers in ascending order (e.g -15, -2, 1, 5, 29)
    matches.sort(key=lambda item: item["days_left"])
    return matches

"""
Example io_manager usage
today = date.today()
expiring_soon = filter_near_expiry(records, today=today, threshold_days=30)

for item in expiring_soon:
    name = item["record"]["product"]["Name"]
    days = item["days_left"]
    print(f"{name} expires in {days} day(s)")
"""