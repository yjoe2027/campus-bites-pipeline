# Campus Bites Pipeline — Agent context

## Purpose

Load synthetic Campus Bites order data from CSV into PostgreSQL, then explore order patterns with SQL or Python. The pipeline is intentionally small: one table, one loader script, and Dockerized Postgres.

## Repository layout

| Path | Role |
|------|------|
| `data/campus_bites_orders.csv` | Source orders (~1.1k rows); authoritative for local analytics if DB is not running |
| `sql/schema.sql` | DDL for the `orders` table |
| `load_data.py` | Wait for Postgres, apply schema, load CSV, run sample SQL checks |
| `docker-compose.yml` | Postgres 16 service (`campus_bites` database) |

There is no `requirements.txt`; the loader expects **Python 3** with **psycopg2** and **pandas** installed.

## Run locally

1. Start Postgres:

   ```bash
   docker compose up -d
   ```

2. From the repo root, run the loader (expects host `localhost`, port `5432`):

   ```bash
   python load_data.py
   ```

The script retries the DB connection (default 10 attempts, 2s apart) so it works while the container finishes starting.

## Database connection

Values are mirrored in `load_data.py` (`DB_CONFIG`) and `docker-compose.yml`:

- **Host:** `localhost`
- **Port:** `5432`
- **Database:** `campus_bites`
- **User:** `campus`
- **Password:** `bites`

Container name: `campus_bites_db`.

## Schema: `orders`

| Column | Type | Notes |
|--------|------|--------|
| `order_id` | INTEGER PK | `ON CONFLICT DO NOTHING` on load |
| `order_date` | DATE | |
| `order_time` | TIME | |
| `customer_segment` | VARCHAR(50) | e.g. Grad Student, Off-Campus, Dorm, Greek Life |
| `order_value` | NUMERIC(10,2) | Revenue per order |
| `cuisine_type` | VARCHAR(50) | |
| `delivery_time_mins` | INTEGER | |
| `promo_code_used` | BOOLEAN | CSV uses Yes/No; loader normalizes to boolean |
| `is_reorder` | BOOLEAN | CSV uses Yes/No; loader normalizes to boolean |

## Data conventions

- CSV boolean columns (`promo_code_used`, `is_reorder`) are **Yes**/**No** strings; `load_data.py` converts them before insert.
- Re-running the loader skips duplicate `order_id` values.

## Sample questions (recompute on current data)

These illustrate typical analyses; numbers depend on the CSV version:

- Average **order value by `customer_segment`** (historically Greek Life ranked highest on the bundled extract).
- Total **revenue by `cuisine_type`** (sum of `order_value`); Pizza/Burgers/Asian often lead on the same extract.
- **Month-over-month revenue:** aggregate by calendar month on `order_date`, then compute \((\text{current} - \text{prior}) / \text{prior}\); watch for seasonal drops after peaks.

Prefer SQL against `orders` when the DB is up; otherwise aggregate the CSV directly.

## Conventions for changes

- Keep schema and `load_data.py` insert list in sync if columns change.
- Avoid hardcoding analytics conclusions in code comments; derive from queries or document assumptions in commit messages.
