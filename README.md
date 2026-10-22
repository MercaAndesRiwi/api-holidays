# api-holidays — Public Holidays Ingestion Microservice

Autonomous, self-contained batch ingestion service that extracts public holiday records from the [Nager.Date API v4](https://nagerholidays.com/) for MercadAndes operational countries and idempotently persists them into a PostgreSQL database.

---

## Overview

`api-holidays` is designed as a standalone ETL batch worker (executable as a CLI script or Docker container). It fetches official public holiday calendars, performs health checks and pre-validations, creates the destination schema automatically if missing, and executes batch upsert operations to ensure data integrity without duplicate records.

### Key Capabilities

- **Multi-Country Support:** Ingests official holidays for Colombia (`CO`), Peru (`PE`), Ecuador (`EC`), Bolivia (`BO`), and Chile (`CL`).
- **Idempotent Persistence:** Automatically creates `public.holidays` and executes atomic batch upserts (`ON CONFLICT (country_code, holiday_date, holiday_name) DO UPDATE`).
- **Resilient HTTP Communication:** Powered by `httpx` with exponential backoff retry logic and connection timeouts to handle temporary external API outages.
- **Strict SOLID Architecture:** Decoupled business logic through `typing.Protocol` interfaces, ensuring dependency inversion and extensibility.
- **Autonomous Health Checks:** Validates environment variables, PostgreSQL database connectivity, and external API responsiveness prior to processing.

---

## Architecture & Design Principles (SOLID)

The service is structured according to clean architecture and SOLID design principles:

- **Single Responsibility Principle (SRP):** Each module handles one distinct concern:
  - [`src/holidays/protocols.py`](src/holidays/protocols.py): Domain contracts and abstractions.
  - [`src/holidays/service.py`](src/holidays/service.py): High-level ingestion orchestration.
  - [`src/holidays/client.py`](src/holidays/client.py): External HTTP communication with Nager.Date.
  - [`src/holidays/repository.py`](src/holidays/repository.py): Database access and batch upsert statements.
  - [`src/holidays/main.py`](src/holidays/main.py): Composition root and pre-execution validations.
- **Open/Closed Principle (OCP):** `HolidayIngestionService` accepts any provider or repository conforming to the defined protocols. New providers (e.g., Google Calendar, custom internal APIs) or persistence targets (e.g., Snowflake, BigQuery) can be added without modifying the service.
- **Liskov Substitution Principle (LSP):** Any provider implementing `HolidaysProvider` can substitute `NagerDateClient` without breaking the ingestion workflow.
- **Interface Segregation Principle (ISP):** Protocols expose strictly the necessary methods (`fetch_holidays` for providers; `create_table_if_not_exists` and `upsert_holidays` for repositories).
- **Dependency Inversion Principle (DIP):** The orchestrator depends solely on abstractions, never on concrete HTTP or database implementations.

---

## Database Schema

The service creates and manages the following table structure:

```sql
CREATE TABLE IF NOT EXISTS public.holidays (
    holiday_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country_code VARCHAR(2) NOT NULL,
    holiday_date DATE NOT NULL,
    holiday_name VARCHAR(150) NOT NULL,
    source VARCHAR(100) NOT NULL,
    CONSTRAINT uq_holiday_country_date_name
        UNIQUE (country_code, holiday_date, holiday_name)
);
```

When re-ingesting holidays, existing records matching `(country_code, holiday_date, holiday_name)` are updated rather than duplicated.

---

## Project Structure

```text
api-holidays/
├── pyproject.toml              # Dependencies, build tools, pytest & ruff configs
├── uv.lock                     # Locked dependency tree (Astral uv)
├── Dockerfile                  # Multi-stage production container build
├── .env.example                # Template for required environment variables
├── .gitignore                  # Git ignore definitions
├── README.md                   # Project documentation
├── .github/
│   └── workflows/
│       └── ci.yml              # CI workflow (linting, tests, container publishing)
├── src/
│   └── holidays/
│       ├── __init__.py         # Package entry
│       ├── config.py           # Environment variables configuration loader
│       ├── db.py               # PostgreSQL SQLAlchemy engine factory
│       ├── protocols.py        # Domain protocols (HolidaysProvider, HolidaysRepositoryProtocol)
│       ├── client.py           # Nager.Date HTTP client with retry logic (httpx)
│       ├── repository.py       # PostgreSQL batch repository
│       ├── service.py          # HolidayIngestionService domain orchestrator
│       └── main.py             # Composition root and CLI entry point
└── tests/
    └── unit/
        ├── test_client.py      # HTTP client, retries, and error handling unit tests
        ├── test_repository.py  # Repository batch statements unit tests
        └── test_service.py     # Domain service orchestration and LSP tests
```

---

## Environment Variables

| Variable | Description | Required | Default |
| :--- | :--- | :---: | :--- |
| `POS_DB_HOST` | PostgreSQL host | Yes | `localhost` |
| `POS_DB_PORT` | PostgreSQL port | Yes | `5432` |
| `POS_DB_NAME` | Database name | Yes | — |
| `POS_DB_USER` | Database user | Yes | — |
| `POS_DB_PASSWORD` | Database user password | Yes | — |
| `API_URL` | Nager.Date base URL | No | `https://nagerholidays.com/api/v4/Holidays` |
| `YEARS` | Comma-separated list of years to process | No | `2026` |
| `COUNTRY_CODES` | Comma-separated list of country ISO codes | No | `CO,PE,EC,BO,CL` |

---

## Getting Started

### Prerequisites

- [Python 3.13+](https://www.python.org/)
- [uv](https://github.com/astral-sh/uv) package manager
- [Docker](https://www.docker.com/) (optional, for containerized execution)

---

### Local Execution

1. **Clone the repository and set up environment variables:**
   ```powershell
   Copy-Item .env.example .env
   # Edit .env with your PostgreSQL credentials
   ```

2. **Install dependencies:**
   ```powershell
   uv sync --locked
   ```

3. **Run the ingestion process:**
   ```powershell
   $env:PYTHONPATH="src"; uv run python -m holidays.main
   ```

---

### Running with Docker

1. **Build the container image:**
   ```bash
   docker build -t api-holidays:latest .
   ```

2. **Execute with your `.env` file:**
   ```bash
   docker run --rm --env-file .env api-holidays:latest
   ```

3. **Execute connecting to a Docker network:**
   ```bash
   docker run --rm --network holidays-net \
     -e POS_DB_HOST=holidays-db \
     -e POS_DB_PORT=5432 \
     -e POS_DB_NAME=api \
     -e POS_DB_USER=postgres \
     -e POS_DB_PASSWORD=secret \
     -e YEARS=2026 \
     -e COUNTRY_CODES=CO,PE,EC,BO,CL \
     api-holidays:latest
   ```

---

## Running Tests and Quality Checks

### Unit Tests
The test suite covers HTTP client logic (mocked responses, error states, exponential backoff retries), repository DDL and batch upsert statements, and domain service orchestration:

```powershell
uv run pytest
```

### Linting and Code Formatting
Quality checks are managed through [Ruff](https://github.com/astral-sh/ruff):

```powershell
uv run ruff check
```

---

## CI/CD Pipeline

On every push or pull request to `main` or `develop`, [GitHub Actions](.github/workflows/ci.yml) executes:

1. `uv sync --locked --dev` — Installs dependencies from lockfile.
2. `uv run ruff check` — Verifies code style and static analysis.
3. `uv run pytest` — Runs unit test suite.
4. **Container Build & Push** — Builds multi-stage Docker image and pushes to GitHub Container Registry (GHCR).
