# Expiry & Discount Advisor — INF1103 Phase 2

## Structure

- `main.py`: `ExpiryAdvisorApp` coordinates the four managers.
- `classes/IO_Manager.py`: terminal input validation and result display.
- `AIManager/AIManager.py`: AI prompting, parsing, and response validation.
- `AIManager/AIService.py` and `GeminiClient.py`: abstract AI contract and Gemini implementation.
- `classes/logicManagerClass.py`: OOP discount rules, configurable category maximum discounts (not fixed overrides) and global maximum.
- `data_manager/data_manager.py`: local-first persistence and optional MongoDB sync.
- `data_manager/RecordRepository.py`: abstract repository with JSON and MongoDB implementations.
- `data_manager/AssessmentRecord.py`: validated encapsulated assessment records.
- `tests/`: offline tests for business rules, AI response validation, records, persistence failure handling, and four-manager workflows.

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
7. Configure discount limits (view, set global cap, set/reset category cap).
0. Exit.

## Configure category discount ceilings

Choose menu **7** → **2** to set the global maximum to **80%**, then
**7** → **3** → **Meat & Seafood** → **70%**. Setting a category cap to 70%
does **not** force the discount to 70%; it only limits the AI/rule recommendation.

Example: with global 80% and category 70%, a 20% recommendation remains
20%, while an 85% recommendation is capped at 70%. Expired items and
AI failures still go through the existing safety/manual-review rules.

The global maximum defaults to 50%, so it must be raised to at least 70%
to allow a 70% category ceiling. Other categories still use the global
maximum unless a separate cap is configured. The existing urgent-risk rule
may raise an AI recommendation to its 30% minimum, subject to both caps.

Settings are saved separately in **data/discount_settings.json** by
DataManager and persist between runs when `data/` is mounted in Docker.
**The settings file is local-only and is not currently synced to MongoDB.**
Assessment records retain the existing JSON-to-MongoDB sync.

For Windows Docker Desktop with MongoDB running on Windows, set
`MONGODB_URI=mongodb://host.docker.internal:27017/` in the private `.env`.

```powershell
docker build -f dockerfile -t expiry-advisor .
docker run --rm --entrypoint python expiry-advisor -m pytest -v
docker run --rm -it --env-file .env -v "${PWD}/data:/app/data" expiry-advisor
```

## Automated tests and Docker

Build the image and run the offline test suite inside Docker:

```bash
python -m pytest -v
docker build -f dockerfile -t expiry-advisor .
docker run --rm --entrypoint python expiry-advisor -m pytest -v
```

### Option 1: External MongoDB URI and Gemini API key (standalone Docker)

Using a `.env` file (copy `.env.example` to `.env` and set `GEMINI_API_KEY` and `MONGODB_URI`, e.g. a MongoDB Atlas `mongodb+srv://...` URI or `mongodb://host.docker.internal:27017/`):

```bash
docker run --rm -it --env-file .env --add-host=host.docker.internal:host-gateway -v "${PWD}/data:/app/data" expiry-advisor
```

Or pass `GEMINI_API_KEY` and `MONGODB_URI` directly on the command line without a `.env` file:

```bash
docker run --rm -it \
  -e GEMINI_API_KEY="your_gemini_api_key" \
  -e MONGODB_URI="mongodb+srv://user:password@cluster.mongodb.net/" \
  -e MONGODB_DATABASE="expiry_advisor" \
  -e MONGODB_COLLECTION="assessments" \
  --add-host=host.docker.internal:host-gateway \
  -v "${PWD}/data:/app/data" \
  expiry-advisor
```

If you have no `.env` file and no external credentials, omit `--env-file .env` / `-e` flags to run with local JSON storage and manual-review fallback.

### Option 2: Docker Compose with bundled live MongoDB

Starts a live MongoDB 7 container and runs the interactive CLI connected to it (reads `GEMINI_API_KEY` from `.env` if present):

```bash
docker compose run --rm app
```

To use an external `MONGODB_URI` with Compose without starting the local `mongo` container:

```bash
docker compose run --rm --no-deps -e GEMINI_API_KEY="your_gemini_api_key" -e MONGODB_URI="mongodb+srv://user:password@cluster.mongodb.net/" app
```

When finished, stop the Compose MongoDB container with:

```bash
docker compose down
```

### Continuous Integration (CI)

The GitHub Actions workflow in `.github/workflows/tests.yml` (**Python tests**) runs automatically on:
- `push` to `main` or `integration`
- any `pull_request`

It sets up Python `3.12` on `ubuntu-latest`, installs dependencies (`python -m pip install -r requirements.txt`), and runs the offline test suite (`python -m pytest -v`) without requiring a live Gemini API key or MongoDB connection.

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
