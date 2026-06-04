"""
Win target selection tests.

Run: py tools/test_win_targets.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from db.loader import load_catalog
from server.win_targets import eligible_win_targets, pick_match_win_target


def test_pool_excludes_bread():
    print("\n--- Win targets: pool excludes bread ---")
    cat = load_catalog()
    pool = dict(eligible_win_targets(cat))
    assert "bread" not in pool
    assert "cake" in pool
    assert "sausage" in pool
    print("  [OK] harder products only:", sorted(pool.keys()))


def test_deterministic_per_match():
    print("\n--- Win targets: same match -> same goal ---")
    cat = load_catalog()
    a = pick_match_win_target(cat, "match-abc", "JOIN01")
    b = pick_match_win_target(cat, "match-abc", "JOIN01")
    c = pick_match_win_target(cat, "match-xyz", "JOIN02")
    assert a == b
    assert a in dict(eligible_win_targets(cat))
    print(f"  [OK] match-abc -> {a}, other match -> {c}")


def test_override_env():
    print("\n--- Win targets: FARM_WARS_WIN_PRODUCT ---")
    cat = load_catalog()
    os.environ["FARM_WARS_WIN_PRODUCT"] = "cheese"
    try:
        assert pick_match_win_target(cat, "m1", "X") == "cheese"
        print("  [OK] override works")
    finally:
        del os.environ["FARM_WARS_WIN_PRODUCT"]


def main():
    print("=" * 50)
    print("WIN TARGET TESTS")
    print("=" * 50)
    if not os.path.isfile(os.path.join(ROOT, "db", "farm_wars.db")):
        print("Run: py tools/init_db.py --seed", file=sys.stderr)
        return 1
    test_pool_excludes_bread()
    test_deterministic_per_match()
    test_override_env()
    print("\n" + "=" * 50)
    print("ALL WIN TARGET CHECKS PASSED")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
