import time
import psycopg2
import pandas as pd
from pathlib import Path

# Connection settings for the local PostgreSQL container
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "campus_bites",
    "user": "campus",
    "password": "bites",
}

# Paths to the CSV data file and SQL schema definition
CSV_PATH = Path("data/campus_bites_orders.csv")
SCHEMA_PATH = Path("sql/schema.sql")


def wait_for_postgres(retries=10, delay=2):
    # Retry the connection on a loop in case the container is still starting up
    for attempt in range(1, retries + 1):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            conn.close()
            print("PostgreSQL is ready.")
            return
        except psycopg2.OperationalError:
            print(f"Waiting for PostgreSQL... ({attempt}/{retries})")
            time.sleep(delay)
    raise RuntimeError("Could not connect to PostgreSQL after several retries.")


def create_table(conn):
    # Read and execute the schema SQL to create the orders table if it doesn't exist
    schema_sql = SCHEMA_PATH.read_text()
    with conn.cursor() as cur:
        cur.execute(schema_sql)
    conn.commit()
    print("Table created (or already exists).")


def load_csv(conn):
    # Load the CSV into a DataFrame
    df = pd.read_csv(CSV_PATH)

    # Normalize Yes/No columns to booleans
    for col in ("promo_code_used", "is_reorder"):
        df[col] = df[col].str.strip().str.upper() == "YES"

    # Insert each row; skip duplicates based on order_id
    with conn.cursor() as cur:
        for _, row in df.iterrows():
            cur.execute(
                """
                INSERT INTO orders (
                    order_id, order_date, order_time, customer_segment,
                    order_value, cuisine_type, delivery_time_mins,
                    promo_code_used, is_reorder
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (order_id) DO NOTHING
                """,
                (
                    row["order_id"],
                    row["order_date"],
                    row["order_time"],
                    row["customer_segment"],
                    row["order_value"],
                    row["cuisine_type"],
                    row["delivery_time_mins"],
                    row["promo_code_used"],
                    row["is_reorder"],
                ),
            )
    conn.commit()
    print(f"Loaded {len(df)} rows into 'orders'.")


def sample_queries(conn):
    # Run a few queries to verify the data loaded correctly and explore basic patterns
    queries = [
        ("Total orders", "SELECT COUNT(*) FROM orders;"),
        ("Avg order value by cuisine", """
            SELECT cuisine_type, ROUND(AVG(order_value), 2) AS avg_value
            FROM orders
            GROUP BY cuisine_type
            ORDER BY avg_value DESC;
        """),
        ("Promo code usage rate", """
            SELECT
                ROUND(100.0 * SUM(CASE WHEN promo_code_used THEN 1 ELSE 0 END) / COUNT(*), 1) AS promo_pct
            FROM orders;
        """),
    ]

    with conn.cursor() as cur:
        for label, sql in queries:
            print(f"\n--- {label} ---")
            cur.execute(sql)
            for row in cur.fetchall():
                print(row)


if __name__ == "__main__":
    # Wait for the database, then create the table, load data, and run sample queries
    wait_for_postgres()
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        create_table(conn)
        load_csv(conn)
        sample_queries(conn)
    finally:
        conn.close()
