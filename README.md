# Expiry & Discount Advisor — INF1103 Phase 2

## Structure

- `main.py`: `ExpiryAdvisorApp` coordinates the four managers.
- `classes/IO_Manager.py`: terminal input validation and result display.
- `AIManager/AIManager.py`: AI prompting, parsing, and response validation.
- `AIManager/AIService.py` and `GeminiClient.py`: abstract AI contract and Gemini implementation.
- `classes/logicManagerClass.py`: OOP discount rules and configurable category maximum discounts (not fixed overrides).
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
7. Configure discount limits (view, set/reset category cap).
0. Exit.

## Configure category discount ceilings

Choose menu **7** -> **2** -> **Meat & Seafood** -> **70%**.
The overall limit is fixed at 100%; only category caps are configurable.
A 20% recommendation remains 20%, while an 85% recommendation is capped
at 70%. Unconfigured categories default to 50%; Other defaults to 20%.
Use submenu option **3** to reset a category to its default.
Expired items and AI failures retain their safety/manual-review rules.
The urgent-risk rule may raise a recommendation to 30%, subject to the
category cap and fixed overall limit.

Settings are saved separately in `data/discount_settings.json` by `DataManager`
and persist between runs when `data/` is mounted in Docker.
**The settings file is local-only and is not synced to MongoDB** (only
assessment records in `data/products.json` sync to MongoDB).

## Automated tests and Docker

Build the image and run the offline test suite (locally or in Docker):

```bash
python -m pytest -v
docker build -f dockerfile -t expiry-advisor .
docker run --rm --entrypoint python expiry-advisor -m pytest -v
```

### Running with Docker (`docker run`)

Using `.env` (with `GEMINI_API_KEY` and `MONGODB_URI`, e.g. the provided Atlas `mongodb+srv://...` URI or `mongodb://host.docker.internal:27017/` for a host-installed MongoDB):

```bash
docker run --rm -it --env-file .env --add-host=host.docker.internal:host-gateway -v "${PWD}/data:/app/data" expiry-advisor
```

Or pass credentials directly without a `.env` file:

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

Omit `--env-file .env` / `-e` flags to run offline with local JSON storage and manual-review fallback.

### Cloud MongoDB (Atlas) setup & limitations

The MongoDB Atlas cluster is **already set up** with a database user (username and password provided separately).

1. Paste the provided `MONGODB_URI` and `GEMINI_API_KEY` into `.env` (or pass them via `-e` above).
2. Run the `docker run` command above and confirm startup prints `Loaded <n> saved record(s) (mongodb).`.

**Limitations:**
- **Single-instance design**: Run one app instance at a time; concurrent multi-user edits are not merged.
- **Empty cloud cluster overwrites unflagged local JSON**: If the cloud collection is empty and `data/products.json` has `sync_pending: false`, startup refreshes `data/products.json` from the cloud (`[]`).
- **Network dependency**: Requires outbound DNS SRV + TLS access to Atlas (timeouts: `8s` server selection, `5s` connect, `10s` socket). If Atlas is unreachable, writes stay local (`sync_pending: true`) until reconnect.

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
