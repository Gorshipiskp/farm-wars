"""
Verify seed_minimal.sql meets TZ minimum counts.

Usage from repo root:
    py tools/init_db.py --seed
    py tools/verify_seed.py
"""

import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "db", "farm_wars.db")

EXPECTED = {
    "plants": 6,
    "animals": 4,
    "recipes": 8,
    "random_events": 1,
    "sabotages": 1,
    "countermeasures": 1,
}


def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def main():
    if not os.path.isfile(DB_PATH):
        print(f"Database not found: {DB_PATH}", file=sys.stderr)
        print("Run: py tools/init_db.py --seed", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        errors = []
        for table, minimum in EXPECTED.items():
            n = count(conn, table)
            if n < minimum:
                errors.append(f"{table}: expected >= {minimum}, got {n}")
            else:
                print(f"  [OK] {table}: {n}")

        bread = conn.execute(
            "SELECT recipe_id, output_product_id, price_override FROM recipes WHERE recipe_id = 'bread'"
        ).fetchone()
        if bread is None or bread["output_product_id"] != "bread":
            errors.append("win target recipe 'bread' missing or wrong output_product_id")
        else:
            print("  [OK] win target: bread -> product bread")

        cake = conn.execute(
            "SELECT price_override FROM recipes WHERE recipe_id = 'cake'"
        ).fetchone()
        if cake is None or cake["price_override"] is None:
            errors.append("recipe 'cake' should have price_override for formula tests")
        else:
            print(f"  [OK] cake price_override: {cake['price_override']}")

        bakery = conn.execute(
            "SELECT time_coef FROM buildings WHERE building_type = 'BAKERY'"
        ).fetchone()
        if bakery is None:
            errors.append("BAKERY building missing")
        else:
            print(f"  [OK] BAKERY time_coef: {bakery['time_coef']}")

        if errors:
            print("\nFAILED:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)

        print("\nAll seed checks passed.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
