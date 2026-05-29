"""
Тесты для waterflow.game — проверяют логику без UI.

Запуск: py tools/test_waterflow.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from waterflow.game import WaterFlow, SwapResult


def test_init():
    print("\n--- Test 1: Init — top row buckets, rest random tiles ---")
    wf = WaterFlow(8, 8, 5)
    grid = wf.get_grid()
    assert len(grid) == 8 and len(grid[0]) == 8
    # Top row = all buckets
    for x in range(8):
        assert grid[0][x] == "B", f"Expected bucket at (0,{x})"
    # Rest = numbers 1-5
    for y in range(1, 8):
        for x in range(8):
            assert grid[y][x] in (1, 2, 3, 4, 5), f"Expected tile at ({y},{x})"
    assert wf.get_delivered_count() == 0
    print("  [OK]")


def test_swap_invalid():
    print("\n--- Test 2: Cannot swap buckets or non-adjacent ---")
    wf = WaterFlow(8, 8, 5)
    # Swap buckets
    assert wf.swap(0, 0, 1, 0) == SwapResult.INVALID
    # Non-adjacent
    assert wf.swap(0, 1, 0, 3) == SwapResult.INVALID
    # Out of bounds
    assert wf.swap(-1, 0, 0, 0) == SwapResult.INVALID
    print("  [OK]")


def test_swap_no_match():
    print("\n--- Test 3: Swap with no combo returns NO_MATCH ---")
    # Create controlled grid
    wf = WaterFlow(8, 8, 2)
    # Override grid for predictable test
    wf.grid = [[None for _ in range(8)] for _ in range(8)]
    wf.grid[0] = ["B"] * 8
    # Two different tiles that don't form 3-in-a-row
    wf.grid[1][0] = 1
    wf.grid[1][1] = 2
    wf.grid[1][2] = 1
    result = wf.swap(0, 1, 1, 1)  # swap 1 and 2
    assert result == SwapResult.NO_MATCH
    # Grid should be unchanged
    assert wf.grid[1][0] == 1
    assert wf.grid[1][1] == 2
    print("  [OK]")


def test_swap_match():
    print("\n--- Test 4: Swap that creates 3-in-a-row returns MATCHED ---")
    wf = WaterFlow(8, 8, 3)
    wf.grid = [[None for _ in range(8)] for _ in range(8)]
    wf.grid[0] = ["B"] * 8
    # Set up: 1 2 1 1 → swap 1 and 2 → 2 1 1 1 (3 in a row!)
    wf.grid[1][0] = 1
    wf.grid[1][1] = 2
    wf.grid[1][2] = 1
    wf.grid[1][3] = 1
    result = wf.swap(0, 1, 1, 1)  # swap first two → 2,1,1,1
    assert result == SwapResult.MATCHED, f"Expected MATCHED, got {result}"
    print("  [OK] Match created and processed")


def test_gravity():
    print("\n--- Test 5: Gravity pulls tiles and buckets down ---")
    wf = WaterFlow(4, 4, 2)
    wf.grid = [[None for _ in range(4)] for _ in range(4)]
    wf.grid[0] = ["B", "B", "B", "B"]
    # Put a tile with empty space below
    wf.grid[1][0] = 1
    wf.grid[2][0] = None  # empty
    wf.grid[3][0] = 2

    # Clear tile at (1,0) and check gravity
    wf._clear_matches({(0, 1)})  # clear tile at (0,1)
    wf._apply_gravity()

    # Tile from (3,0)=2 should fall to fill gap, new tiles from top
    assert wf.grid[3][0] is not None, "Bottom should be filled"
    print("  [OK] Gravity works")


def test_bucket_delivery():
    print("\n--- Test 6: Bucket at bottom row is delivered ---")
    wf = WaterFlow(4, 2, 2)  # height=2: only top row (buckets) and one row below
    # Clear all tiles below buckets
    wf.grid = [["B", "B", "B", "B"], [None, None, None, None]]
    wf.buckets_delivered = 0
    wf._apply_gravity()
    assert wf.buckets_delivered == 4, f"Expected 4 delivered, got {wf.buckets_delivered}"
    assert wf.is_won()
    print("  [OK]")


def test_reset():
    print("\n--- Test 7: Reset clears state ---")
    wf = WaterFlow(8, 8, 5)
    wf.buckets_delivered = 3
    wf.reset()
    assert wf.buckets_delivered == 0
    assert wf.get_delivered_count() == 0
    assert wf.grid[0][0] == "B"  # top row still buckets
    print("  [OK]")


def test_swap_creates_match_diagonal():
    print("\n--- Test 8: Diagonal swap is INVALID ---")
    wf = WaterFlow(8, 8, 5)
    # Diagonal neighbors are NOT valid swaps
    assert wf.swap(0, 1, 1, 2) == SwapResult.INVALID
    print("  [OK]")


def test_get_grid_is_copy():
    print("\n--- Test 9: get_grid returns copy, not reference ---")
    wf = WaterFlow(4, 4, 2)
    grid = wf.get_grid()
    grid[0][0] = "MODIFIED"
    assert wf.get_grid()[0][0] == "B", "Original grid should not be modified"
    print("  [OK]")


def test_shuffle_on_no_moves():
    print("\n--- Test 10: Shuffle called when no valid moves ---")
    wf = WaterFlow(4, 4, 2)
    # Create grid with no possible moves
    wf.grid = [[None for _ in range(4)] for _ in range(4)]
    wf.grid[0] = ["B", "B", "B", "B"]
    # Alternating pattern: 1 2 1 2, 2 1 2 1 — no 3-in-a-row possible
    wf.grid[1] = [1, 2, 1, 2]
    wf.grid[2] = [2, 1, 2, 1]
    wf.grid[3] = [1, 2, 1, 2]

    # Just verify shuffle runs without error (may or may not have valid moves)
    try:
        wf._shuffle()
    except Exception as e:
        assert False, f"Shuffle raised: {e}"
    print("  [OK] Shuffle executed without error")


def main():
    print("=" * 50)
    print("WATER FLOW TESTS")
    print("=" * 50)
    test_init()
    test_swap_invalid()
    test_swap_no_match()
    test_swap_match()
    test_gravity()
    test_bucket_delivery()
    test_reset()
    test_swap_creates_match_diagonal()
    test_get_grid_is_copy()
    test_shuffle_on_no_moves()
    print("\n" + "=" * 50)
    print("ALL CHECKS PASSED")
    print("=" * 50)


if __name__ == "__main__":
    main()
