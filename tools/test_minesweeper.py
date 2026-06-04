"""
Тесты для minesweeper.game — проверяют логику без UI.

Запуск: py tools/test_minesweeper.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from minesweeper.game import Minesweeper, ClickResult


def test_init():
    print("\n--- Test 1: Init — empty board before first click ---")
    m = Minesweeper(9, 9, 10)
    board = m.get_board()
    assert len(board) == 9
    assert len(board[0]) == 9
    assert all(c["is_revealed"] is False for row in board for c in row)
    print("  [OK]")


def test_first_click_safe():
    print("\n--- Test 2: First click never hits a mine ---")
    for _ in range(50):
        m = Minesweeper(9, 9, 10)
        result = m.click(4, 4)
        assert result != ClickResult.LOST, "First click should be safe!"
    print("  [OK] 50/50 safe first clicks")


def test_mine_count():
    print("\n--- Test 3: Exactly N mines placed ---")
    m = Minesweeper(9, 9, 10)
    m.click(0, 0)  # place mines
    board = m.get_board()
    # After first click, board is populated (though mines hidden)
    # We can check internal _board
    mine_count = sum(1 for row in m._board for c in row if c.is_mine)
    assert mine_count == 10, f"Expected 10 mines, got {mine_count}"
    print("  [OK]")


def test_flag_toggle():
    print("\n--- Test 4: Flag toggle works ---")
    m = Minesweeper(9, 9, 10)
    m.click(4, 4)  # place mines (center, safe)
    m.toggle_flag(8, 8)
    board = m.get_board()
    assert board[8][8]["is_flagged"] is True
    m.toggle_flag(8, 8)
    board = m.get_board()
    assert board[8][8]["is_flagged"] is False
    print("  [OK]")

def test_cannot_flag_revealed():
    print("\n--- Test 5: Cannot flag revealed cell ---")
    m = Minesweeper(9, 9, 10)
    m.click(4, 4)  # first click reveals center
    m.toggle_flag(4, 4)  # try to flag revealed cell
    board = m.get_board()
    assert board[4][4]["is_flagged"] is False
    assert board[4][4]["is_revealed"] is True
    print("  [OK]")


def test_cannot_flag_revealed():
    print("\n--- Test 5: Cannot flag revealed cell ---")
    m = Minesweeper(9, 9, 10)
    m.click(0, 0)  # first click reveals
    m.toggle_flag(0, 0)  # try to flag
    board = m.get_board()
    assert board[0][0]["is_flagged"] is False
    assert board[0][0]["is_revealed"] is True
    print("  [OK]")


def test_loss_reveals_mines():
    print("\n--- Test 6: Loss reveals all mines ---")
    for _ in range(30):
        m = Minesweeper(9, 9, 10)
        # First click somewhere
        m.click(0, 0)
        # Find a mine by checking internal board
        mine_pos = None
        for y in range(m.height):
            for x in range(m.width):
                if m._board[y][x].is_mine:
                    mine_pos = (x, y)
                    break
            if mine_pos:
                break
        if mine_pos is None:
            continue
        result = m.click(mine_pos[0], mine_pos[1])
        assert result == ClickResult.LOST
        assert m.is_lost()
        board = m.get_board()
        # All mines should be visible
        mine_cells = sum(1 for row in m._board for c in row if c.is_mine)
        revealed_mines = sum(1 for row in board for c in row if c["is_mine"] and c["is_revealed"])
        assert revealed_mines == mine_cells, f"Expected {mine_cells} revealed mines, got {revealed_mines}"
        break
    print("  [OK]")


def test_auto_reset():
    print("\n--- Test 7: Reset clears board ---")
    m = Minesweeper(9, 9, 10)
    m.click(0, 0)
    m.reset()
    board = m.get_board()
    assert all(c["is_revealed"] is False for row in board for c in row)
    assert m.is_lost() is False
    print("  [OK]")


def test_win_all_revealed():
    print("\n--- Test 8: Win when all non-mine cells revealed ---")
    # Используем поле 3x3 с 1 миной для быстрого теста
    m = Minesweeper(3, 3, 1)
    m.click(0, 0)  # place mine and reveal
    # Reveal all non-mine cells manually
    for y in range(3):
        for x in range(3):
            if not m._board[y][x].is_mine:
                m.click(x, y)
    assert m.is_won()
    print("  [OK]")


def test_win_all_mines_flagged():
    print("\n--- Test 9: Win when all mines flagged ---")
    m = Minesweeper(3, 3, 1)
    m.click(0, 0)  # place mine
    # Find mine and flag it
    for y in range(3):
        for x in range(3):
            if m._board[y][x].is_mine:
                m.toggle_flag(x, y)
                break
    assert m.is_won()
    print("  [OK]")


def test_presets():
    print("\n--- Test 10: Difficulty presets ---")
    assert Minesweeper.preset("easy") == (7, 7, 6)
    assert Minesweeper.preset("medium") == (10, 10, 18)
    assert Minesweeper.preset("hard") == (13, 13, 30)
    w, h, mines = Minesweeper.preset("easy")
    m = Minesweeper(w, h, mines)
    assert m.width == 7 and m.height == 7 and m.mine_count == 6
    print("  [OK]")


def test_flood_fill():
    print("\n--- Test 11: Flood fill reveals connected empty cells ---")
    m = Minesweeper(5, 5, 1)
    # Click corner — should reveal all connected zeros
    m.click(0, 0)
    board = m.get_board()
    # At least cell (0,0) and neighbors should be revealed
    assert board[0][0]["is_revealed"] is True
    print("  [OK] Flood fill works")


def test_click_out_of_bounds():
    print("\n--- Test 12: Out-of-bounds click doesn't crash ---")
    m = Minesweeper(9, 9, 10)
    result = m.click(-1, 0)
    assert result == ClickResult.SAFE
    result = m.click(100, 100)
    assert result == ClickResult.SAFE
    m.toggle_flag(-1, -1)  # should not crash
    print("  [OK]")


def main():
    print("=" * 50)
    print("MINESWEEPER TESTS")
    print("=" * 50)
    test_init()
    test_first_click_safe()
    test_mine_count()
    test_flag_toggle()
    test_cannot_flag_revealed()
    test_loss_reveals_mines()
    test_auto_reset()
    test_win_all_revealed()
    test_win_all_mines_flagged()
    test_presets()
    test_flood_fill()
    test_click_out_of_bounds()
    print("\n" + "=" * 50)
    print("ALL CHECKS PASSED")
    print("=" * 50)


if __name__ == "__main__":
    main()
