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
