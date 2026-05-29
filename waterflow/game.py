"""
Логика мини-игры «Три в ряд с вёдрами» (Water Flow) — без привязки к UI.

Правила:
- Поле 8×8 (настраиваемое). Верхний ряд — вёдра (B).
- Ниже — цветные тайлы 5 типов (1–5).
- Игрок меняет местами два соседних тайла (не вёдра).
- 3+ одинаковых тайла в ряд → исчезают, тайлы падают вниз, новые сверху.
- Вёдра падают вниз под силой тяжести, их нельзя двигать.
- Когда ведро достигает нижнего ряда — оно «доставлено» и исчезает.
- Цель: доставить ВСЕ вёдра в нижний ряд.
- Если нет возможных ходов → поле перемешивается.
- Если после перемешивания всё ещё нет ходов → поражение → авто-рестарт.

Использование:
    from waterflow.game import WaterFlow, SwapResult

    wf = WaterFlow(width=8, height=8, tile_types=5)
    wf.swap(3, 4, 4, 4)  # свап соседних тайлов
    grid = wf.get_grid()
    if wf.is_won(): ...
    if wf.is_lost(): wf.reset()
"""

import random
from dataclasses import dataclass
from enum import Enum, auto


class SwapResult(Enum):
    INVALID = auto()    # нельзя свапнуть (вёдра, не соседи)
    NO_MATCH = auto()   # свап не дал комбинации
    MATCHED = auto()    # комбинация найдена, поле обновлено
    WIN = auto()        # все вёдра доставлены
    LOST = auto()       # нет ходов + шаффл не помог


BUCKET = "B"
EMPTY = None

DEFAULT_WIDTH = 8
DEFAULT_HEIGHT = 8
DEFAULT_TILE_TYPES = 5


class WaterFlow:
    """
    Ядро мини-игры «Три в ряд с вёдрами».
    Параметры: width, height — размер поля; tile_types — сколько цветов (2–9).
    """

    def __init__(self, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT,
                 tile_types: int = DEFAULT_TILE_TYPES):
        if width < 3 or height < 2:
            raise ValueError("Grid too small")
        if tile_types < 2:
            raise ValueError("Need at least 2 tile types")
        self.width = width
        self.height = height
        self.tile_types = tile_types
        self.total_buckets = width  # по одному на колонку в верхнем ряду
        self.buckets_delivered = 0
        self.grid: list[list] = []
        self._init_grid()

    # ----- Публичные методы -----

    def swap(self, x1: int, y1: int, x2: int, y2: int) -> SwapResult:
        """
        Поменять местами два тайла. Возвращает результат.
        (x1,y1) и (x2,y2) должны быть соседними (манхэттенское расстояние = 1).
        """
        if not (0 <= x1 < self.width and 0 <= y1 < self.height):
            return SwapResult.INVALID
        if not (0 <= x2 < self.width and 0 <= y2 < self.height):
            return SwapResult.INVALID
        if abs(x1 - x2) + abs(y1 - y2) != 1:
            return SwapResult.INVALID
        if self.grid[y1][x1] == BUCKET or self.grid[y2][x2] == BUCKET:
            return SwapResult.INVALID

        # Свап
        self.grid[y1][x1], self.grid[y2][x2] = self.grid[y2][x2], self.grid[y1][x1]

        # Проверить совпадения
        matches = self._find_matches()
        if not matches:
            # Откатить
            self.grid[y1][x1], self.grid[y2][x2] = self.grid[y2][x2], self.grid[y1][x1]
            return SwapResult.NO_MATCH

        # Удалить совпадения, применить гравитацию, заполнить
        self._clear_matches(matches)
        self._apply_gravity()

        # Проверить победу
        if self.buckets_delivered >= self.total_buckets:
            return SwapResult.WIN

        # Проверить, есть ли ходы
        if not self._has_valid_moves():
            self._shuffle()
            if not self._has_valid_moves():
                return SwapResult.LOST

        return SwapResult.MATCHED

    def get_grid(self) -> list[list]:
        """
        Текущее состояние поля для отрисовки.
        Возвращает 2D список: 'B' — ведро, 1..N — цветной тайл, None — пусто.
        """
        return [row[:] for row in self.grid]

    def get_delivered_count(self) -> int:
        """Сколько вёдер доставлено."""
        return self.buckets_delivered

    def is_won(self) -> bool:
        return self.buckets_delivered >= self.total_buckets

    def is_lost(self) -> bool:
        return not self._has_valid_moves()

    def reset(self):
        """Сбросить поле (авто-рестарт)."""
        self.buckets_delivered = 0
        self.grid = []
        self._init_grid()

    # ----- Внутренняя логика -----

    def _init_grid(self):
        """Создать начальное поле: верхний ряд — вёдра, остальное — случайные тайлы."""
        self.grid = [[EMPTY for _ in range(self.width)] for _ in range(self.height)]
        for x in range(self.width):
            self.grid[0][x] = BUCKET
        for y in range(1, self.height):
            for x in range(self.width):
                self.grid[y][x] = random.randint(1, self.tile_types)

    def _find_matches(self) -> set:
        """Найти все комбинации 3+ одинаковых тайлов (не вёдра)."""
        matched = set()

        # Горизонталь
        for y in range(self.height):
            run_start = 0
            for x in range(1, self.width + 1):
                if (x < self.width and
                        self.grid[y][x] is not None and
                        self.grid[y][x] != BUCKET and
                        self.grid[y][x] == self.grid[y][run_start]):
                    continue
                if x - run_start >= 3 and self.grid[y][run_start] is not None:
                    for mx in range(run_start, x):
                        matched.add((mx, y))
                run_start = x

        # Вертикаль
        for x in range(self.width):
            run_start = 0
            for y in range(1, self.height + 1):
                if (y < self.height and
                        self.grid[y][x] is not None and
                        self.grid[y][x] != BUCKET and
                        self.grid[y][x] == self.grid[run_start][x]):
                    continue
                if y - run_start >= 3 and self.grid[run_start][x] is not None:
                    for my in range(run_start, y):
                        matched.add((x, my))
                run_start = y

        return matched

    def _clear_matches(self, matches: set):
        """Удалить совпавшие тайлы."""
        for x, y in matches:
            self.grid[y][x] = EMPTY

    def _apply_gravity(self):
        """
        Тайлы и вёдра падают вниз.
        Вёдра, достигшие нижнего ряда — доставляются.
        Пустоты сверху заполняются случайными тайлами.
        """
        for x in range(self.width):
            # Собрать всё не-пустое в колонке (снизу вверх)
            column = []
            for y in range(self.height - 1, -1, -1):
                if self.grid[y][x] is not EMPTY:
                    column.append(self.grid[y][x])

            # Вёдра в нижнем ряду → доставлены
            new_column = []
            for tile in column:
                new_column.append(tile)

            # Заполнить колонку снизу вверх
            col_idx = 0
            for y in range(self.height - 1, -1, -1):
                if col_idx < len(new_column):
                    tile = new_column[col_idx]
                    # Проверить: ведро на нижнем ряду?
                    if tile == BUCKET and y == self.height - 1:
                        self.buckets_delivered += 1
                        # Не кладём ведро — оно «ушло»
                        self.grid[y][x] = EMPTY
                    else:
                        self.grid[y][x] = tile
                    col_idx += 1
                else:
                    # Пустые клетки сверху → новые случайные тайлы
                    self.grid[y][x] = random.randint(1, self.tile_types)

    def _has_valid_moves(self) -> bool:
        """Есть ли хотя бы один свап, дающий комбинацию?"""
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] is None or self.grid[y][x] == BUCKET:
                    continue
                # Проверить свап с соседом справа
                if x + 1 < self.width and self.grid[y][x + 1] not in (None, BUCKET):
                    if self._would_match(x, y, x + 1, y):
                        return True
                # Проверить свап с соседом снизу
                if y + 1 < self.height and self.grid[y + 1][x] not in (None, BUCKET):
                    if self._would_match(x, y, x, y + 1):
                        return True
        return False

    def _would_match(self, x1, y1, x2, y2) -> bool:
        """Проверить: даст ли свап (x1,y1)↔(x2,y2) комбинацию? (без изменения поля)"""
        self.grid[y1][x1], self.grid[y2][x2] = self.grid[y2][x2], self.grid[y1][x1]
        result = len(self._find_matches()) > 0
        self.grid[y1][x1], self.grid[y2][x2] = self.grid[y2][x2], self.grid[y1][x1]
        return result

    def _shuffle(self):
        """Перемешать все не-ведёрные тайлы (если нет ходов)."""
        tiles = []
        positions = []
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] not in (None, BUCKET):
                    tiles.append(self.grid[y][x])
                    positions.append((x, y))
        random.shuffle(tiles)
        for (x, y), tile in zip(positions, tiles):
            self.grid[y][x] = tile
