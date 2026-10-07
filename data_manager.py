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