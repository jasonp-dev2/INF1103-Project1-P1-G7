# Expiry & Discount Advisor — INF1103 Phase 2

## Structure

- `main.py`: `ExpiryAdvisorApp` coordinates the four managers.
- `classes/IO_Manager.py`: terminal input validation and result display.
- `AIManager/AIManager.py`: AI prompting, parsing, and response validation.
- `AIManager/AIService.py` and `GeminiClient.py`: abstract AI contract and Gemini implementation.
- `classes/logicManagerClass.py`: OOP discount rules, optional category overrides, maximum discount.
- `data_manager/data_manager.py`: local-first persistence and optional MongoDB sync.
- `data_manager/RecordRepository.py`: abstract repository with JSON and MongoDB implementations.
- `data_manager/AssessmentRecord.py`: validated encapsulated assessment records.
- `tests/`: offline tests for business rules, records, JSON and four-manager workflows.

## Setup

Requires Python 3.12 or later. Run from the repository root:

```bash
python -m pip install -r requirements.txt
python main.py
```

Copy `.env.example` to `.env` and set `GEMINI_API_KEY` for live AI assessments.
No Gemini key is required for offline automated tests. If unavailable, new assessments
use the existing manual-review fallback.

MongoDB is optional for offline operation once the local dataset exists.
Set `MONGODB_URI`, `MONGODB_DATABASE`, and `MONGODB_COLLECTION` as needed.
The default is local MongoDB on port 27017. The application keeps a versioned
JSON backup at `data/products.json` and synchronises pending writes on reconnect.

## Menu

1. Assess new product through IO → AI → Logic → Data.
2. Show all product assessments.
3. Filter products expiring within a chosen number of days.
4. View a saved assessment by record ID.
5. Change stock and run a fresh AI/Logic assessment; old staff approval is invalidated.
6. Soft-delete a record by ID (retaining its ID and tombstone for sync).
0. Exit.

## Automated tests and Docker

```bash
python -m pytest -v
docker build -f dockerfile -t expiry-advisor .
docker run --rm -it --env-file .env expiry-advisor
docker run --rm --entrypoint python expiry-advisor -m pytest -v
```

If you have no `.env` file, omit `--env-file .env` from the run command.
GitHub Actions also runs the offline tests on pushes and pull requests.

## Storage safety and legacy records

The authoritative new-format local snapshot is `data/products.json`. The
root-level `products.json` is legacy Phase 1 data with inconsistent keys.
It is retained for archival/migration purposes and is **not loaded automatically**.
Do not delete it until its records have been reviewed and migrated.

If `data/products.json` is damaged, the app **does not overwrite it with
empty records**. Resolve the storage error or restore a valid backup instead.

## Important design notes

- `AssessmentRecord` owns the record state and returns copies via `to_dict()`.
- JSON/MongoDB repositories implement one `RecordRepository` interface.
- `ExpiryAdvisorApp` coordinates; IO never reads/writes JSON or calls AI directly.
- Stock changes re-run AI and business rules to avoid stale risk predictions.
- AI and MongoDB credentials must never be committed to Git.
