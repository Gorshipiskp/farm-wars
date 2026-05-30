"""
Checkpoint 4: verify recipe price formula vs price_override.

Run from repo root (after init_db --seed):
    py tools/test_db_pricing.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from db.loader import load_catalog
from db.pricing import calculate_recipe_price_from_catalog

# bread base: 16+5+60=81; ×1.4 markup → 113
EXPECTED_BREAD_FORMULA = 113
EXPECTED_CAKE_OVERRIDE = 100


def main():
    catalog = load_catalog()

    bread = calculate_recipe_price_from_catalog("bread", catalog)
    assert bread == EXPECTED_BREAD_FORMULA, f"bread: expected {EXPECTED_BREAD_FORMULA}, got {bread}"
    print(f"  [OK] bread formula price: {bread}")

    cake = calculate_recipe_price_from_catalog("cake", catalog)
    assert cake == EXPECTED_CAKE_OVERRIDE, f"cake: expected {EXPECTED_CAKE_OVERRIDE}, got {cake}"
    print(f"  [OK] cake override price: {cake}")

    recipe = catalog.get_recipe("bread")
    assert recipe is not None and recipe.price_override is None
    recipe_cake = catalog.get_recipe("cake")
    assert recipe_cake is not None and recipe_cake.price_override == 100
    print("  [OK] price_override NULL vs set")

    print("\nAll pricing checks passed.")


if __name__ == "__main__":
    main()
