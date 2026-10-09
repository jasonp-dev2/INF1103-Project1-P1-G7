import json

FILE_NAME = "products.json"


# Loads all product records from the JSON file
# Creates a new JSON file if it does not exist
def load_records():
    try:
        file = open(FILE_NAME, "r")
        records = json.load(file)
        file.close()

        return records

    except FileNotFoundError:
        file = open(FILE_NAME, "w")
        json.dump([], file, indent=4)
        file.close()

        return []

    except json.JSONDecodeError:
        return []


# Saves all product records into the JSON file
def save_records(records):
    file = open(FILE_NAME, "w")
    json.dump(records, file, indent=4)
    file.close()


# Creates the next record ID
def create_record_id(records):
    if len(records) == 0:
        return "PRD-0001"

    highest_number = 0

    for record in records:
        record_id = record["record_id"]
        number = int(record_id.replace("PRD-", ""))

        if number > highest_number:
            highest_number = number

    new_number = highest_number + 1

    return "PRD-" + format(new_number, "04d")


# Adds the user's product input into the JSON file
def add_record(product):
    records = load_records()

    record_id = create_record_id(records)

    record = {
        "record_id": record_id,
        "product": product
    }

    records.append(record)

    save_records(records)

    return record


# Updates the existing record after AI and logic processing
def update_record(record_id, ai_assessment, decision):
    records = load_records()

    for record in records:

        if record["record_id"] == record_id:
            record["ai_assessment"] = ai_assessment
            record["decision"] = decision

            save_records(records)

            return record

    return None


# Finds a product record using its record ID
def get_record(record_id):
    records = load_records()

    for record in records:

        if record["record_id"] == record_id:
            return record

    return None


# Returns all records that match a given condition
def query(filter_fn):
    records = load_records()

    matching_records = []

    for record in records:

        if filter_fn(record):
            matching_records.append(record)

    return matching_records