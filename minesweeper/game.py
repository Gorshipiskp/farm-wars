"""
Логика игры «Сапер» (Minesweeper) — без привязки к UI.

Этот модуль отвечает ТОЛЬКО за правила игры:
- генерацию поля с минами,
- открытие клеток и флажки,
- проверку победы/поражения,
- авто-рестарт при поражении.

За рендеринг (pygame-окно, отрисовку клеток, клики мышью)
отвечает NIKITA. См. docs/specs/client/002.NIKITA.MINESWEEPER_UI.md

Использование:
    from minesweeper.game import Minesweeper

    ms = Minesweeper(width=9, height=9, mine_count=10)
    ms.click(3, 4)      # открыть клетку
    ms.toggle_flag(5, 2) # поставить/убрать флажок
    board = ms.get_board()  # получить поле для отрисовки
    if ms.is_won(): ...
    if ms.is_lost(): ms.reset()  # авто-рестарт

Сложность (в будущем):
    Minesweeper.presets = {"easy": (9,9,10), "medium": (12,12,25), "hard": (15,15,40)}
"""

import random
from dataclasses import dataclass, field
from enum import Enum, auto


class ClickResult(Enum):
    """Что случилось после клика."""
    SAFE = auto()       # клетка открыта, игра продолжается
    WIN = auto()        # все мины обезврежены / все клетки открыты
    LOST = auto()       # попал в мину


@dataclass
class _Cell:
    """Внутреннее состояние одной клетки."""
    is_mine: bool = False
    is_revealed: bool = False
    is_flagged: bool = False
    adjacent_mines: int = 0
    is_exploded: bool = False  # клетка, в которую попал игрок (при проигрыше)


DEFAULT_WIDTH = 9
DEFAULT_HEIGHT = 9
DEFAULT_MINES = 10

# Преступы сложности (width, height, mines)
PRESETS = {
    "easy": (9, 9, 10),
    "medium": (12, 12, 25),
    "hard": (15, 15, 40),
}


class Minesweeper:
    """
    Ядро игры «Сапер».

    Параметры:
        width, height — размер поля в клетках
        mine_count — количество мин

    Поле НЕ генерируется при создании — мины расставляются
    после ПЕРВОГО клика, чтобы гарантировать безопасный первый ход.
    """

    def __init__(self, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT,
                 mine_count: int = DEFAULT_MINES):
        if mine_count >= width * height:
            raise ValueError(f"Too many mines ({mine_count}) for {width}x{height} board")
        self.width = width
        self.height = height
        self.mine_count = mine_count
        self._board: list[list[_Cell]] = []
        self._mines_placed = False
        self._first_click = True
        self._revealed_count = 0

    # ----- Публичные методы (для NIKITA) -----

    def click(self, x: int, y: int) -> ClickResult:
        """Открыть клетку (левый клик). Возвращает результат."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return ClickResult.SAFE

        if self._first_click:
            self._place_mines(x, y)
            self._first_click = False

        cell = self._board[y][x]
        if cell.is_revealed or cell.is_flagged:
            return ClickResult.SAFE

        if cell.is_mine:
            # Поражение — показать все мины
            cell.is_exploded = True
            for row in self._board:
                for c in row:
                    if c.is_mine and not c.is_flagged:
                        c.is_revealed = True
            return ClickResult.LOST

        self._reveal(x, y)

        if self._check_win():
            return ClickResult.WIN
        return ClickResult.SAFE

    def toggle_flag(self, x: int, y: int):
        """Поставить или убрать флажок (правый клик)."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        cell = self._board[y][x]
        if cell.is_revealed:
            return
        cell.is_flagged = not cell.is_flagged

        # Проверка победы: все мины помечены флажками
        if self._check_win():
            # Отметим как победу при следующей проверке
            pass

    def is_won(self) -> bool:
        """Победа достигнута?"""
        return self._check_win()

    def is_lost(self) -> bool:
        """Было поражение в текущей игре?"""
        # Если есть взорванная клетка — было поражение
        for row in self._board:
            for c in row:
                if c.is_exploded:
                    return True
        return False

    def reset(self):
        """Сбросить поле (авто-рестарт после поражения или ручной)."""
        self._board = []
        self._mines_placed = False
        self._first_click = True
        self._revealed_count = 0

    def get_board(self) -> list[list[dict]]:
        """
        Получить текущее состояние поля для отрисовки.

        Если поле еще не создано (до первого клика) — возвращает
        сетку из неоткрытых клеток-заглушек.
        """
        if not self._board:
            return [[{"is_mine": False, "is_revealed": False, "is_flagged": False,
                      "adjacent_mines": 0, "is_exploded": False}
                     for _ in range(self.width)] for _ in range(self.height)]
        result = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                cell = self._board[y][x]
                row.append({
                    "is_mine": cell.is_mine if (cell.is_revealed or self.is_lost()) else False,
                    "is_revealed": cell.is_revealed,
                    "is_flagged": cell.is_flagged,
                    "adjacent_mines": cell.adjacent_mines if cell.is_revealed else 0,
                    "is_exploded": cell.is_exploded,
                })
            result.append(row)
        return result

    def get_flagged_count(self) -> int:
        """Сколько флажков поставлено."""
        if not self._board:
            return 0
        count = 0
        for row in self._board:
            for c in row:
                if c.is_flagged:
                    count += 1
        return count

    @staticmethod
    def preset(name: str) -> tuple[int, int, int]:
        """Получить параметры по имени пресета ('easy', 'medium', 'hard')."""
        return PRESETS.get(name, (DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_MINES))

    # ----- Внутренняя логика -----

    def _place_mines(self, safe_x: int, safe_y: int):
        """Расставить мины ПОСЛЕ первого клика. (safe_x, safe_y) и соседи — без мин."""
        self._board = [[_Cell() for _ in range(self.width)] for _ in range(self.height)]

        # Зона безопасности: сама клетка + 8 соседей
        safe_zone = {(safe_x, safe_y)}
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = safe_x + dx, safe_y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    safe_zone.add((nx, ny))

        # Список ВСЕХ возможных позиций, кроме safe_zone
        positions = [(x, y) for y in range(self.height) for x in range(self.width)
                     if (x, y) not in safe_zone]

        # Если безопасная зона слишком большая для оставшихся мин
        if len(positions) < self.mine_count:
            # Разрешаем мины в safe_zone (редкий случай на маленьких полях)
            positions = [(x, y) for y in range(self.height) for x in range(self.width)
                         if (x, y) != (safe_x, safe_y)]

        mine_positions = random.sample(positions, self.mine_count)
        for mx, my in mine_positions:
            self._board[my][mx].is_mine = True

        # Посчитать adjacent_mines для всех клеток
        for y in range(self.height):
            for x in range(self.width):
                if self._board[y][x].is_mine:
                    continue
                count = 0
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if self._board[ny][nx].is_mine:
                                count += 1
                self._board[y][x].adjacent_mines = count

        self._mines_placed = True

    def _reveal(self, x: int, y: int):
        """Открыть клетку. Если пустая (0 мин рядом) — flood fill."""
        cell = self._board[y][x]
        if cell.is_revealed or cell.is_flagged or cell.is_mine:
            return

        cell.is_revealed = True
        self._revealed_count += 1

        if cell.adjacent_mines == 0:
            # Flood fill: открыть всех соседей
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        self._reveal(nx, ny)

    def _check_win(self) -> bool:
        """
        Победа если:
        - все клетки БЕЗ мин открыты (revealed), ИЛИ
        - все мины помечены флажками И нет лишних флажков
        """
        if not self._mines_placed:
            return False

        total_cells = self.width * self.height
        # Все не-минные клетки открыты
        if self._revealed_count >= total_cells - self.mine_count:
            return True

        # Все мины под флажками, и нет флажков на не-минах
        flagged_mines = 0
        flagged_safe = 0
        for row in self._board:
            for c in row:
                if c.is_flagged:
                    if c.is_mine:
                        flagged_mines += 1
                    else:
                        flagged_safe += 1

        if flagged_mines == self.mine_count and flagged_safe == 0:
            return True

        return False
