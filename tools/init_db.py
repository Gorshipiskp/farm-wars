"""
Create db/farm_wars.db from schema.sql (+ optional seed).

Usage from repo root:
    py tools/init_db.py
    py tools/init_db.py --seed
"""

import argparse
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(ROOT, "db")
DB_PATH = os.path.join(DB_DIR, "farm_wars.db")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")
SEED_PATH = os.path.join(DB_DIR, "seed_minimal.sql")


def run_sql_file(conn, path):
    with open(path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())


def main():
    parser = argparse.ArgumentParser(description="Initialize Farm Wars SQLite database")
    parser.add_argument("--seed", action="store_true", help="Apply seed_minimal.sql after schema")
    args = parser.parse_args()

    os.makedirs(DB_DIR, exist_ok=True)
    if os.path.isfile(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        print(f"Applying schema: {SCHEMA_PATH}")
        run_sql_file(conn, SCHEMA_PATH)

        if args.seed:
            if not os.path.isfile(SEED_PATH):
                print(f"Seed file not found: {SEED_PATH}", file=sys.stderr)
                sys.exit(1)
            print(f"Applying seed: {SEED_PATH}")
            run_sql_file(conn, SEED_PATH)

        conn.commit()

        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        print(f"Database ready: {DB_PATH}")
        print("Tables:", ", ".join(t[0] for t in tables))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
