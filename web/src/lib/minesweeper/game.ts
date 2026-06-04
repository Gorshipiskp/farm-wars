import type { BoardCell, ClickResult, MinesweeperPreset } from "./types";

type Cell = {
  is_mine: boolean;
  is_revealed: boolean;
  is_flagged: boolean;
  adjacent_mines: number;
  is_exploded: boolean;
};

const PRESETS: Record<MinesweeperPreset, [number, number, number]> = {
  easy: [7, 7, 6],
  medium: [10, 10, 18],
  hard: [13, 13, 30],
};

const DEFAULT_WIDTH = 9;
const DEFAULT_HEIGHT = 9;
const DEFAULT_MINES = 10;

function stubCell(): BoardCell {
  return {
    is_mine: false,
    is_revealed: false,
    is_flagged: false,
    adjacent_mines: 0,
    is_exploded: false,
  };
}

/** Minesweeper core — port of `minesweeper/game.py` for the web client. */
export class Minesweeper {
  readonly width: number;
  readonly height: number;
  readonly mine_count: number;

  private board: Cell[][] = [];
  private mines_placed = false;
  private first_click = true;
  private revealed_count = 0;

  constructor(
    width: number = DEFAULT_WIDTH,
    height: number = DEFAULT_HEIGHT,
    mine_count: number = DEFAULT_MINES,
  ) {
    if (mine_count >= width * height) {
      throw new Error(`Too many mines (${mine_count}) for ${width}x${height} board`);
    }
    this.width = width;
    this.height = height;
    this.mine_count = mine_count;
  }

  static preset(name: MinesweeperPreset): [number, number, number] {
    return PRESETS[name] ?? [DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_MINES];
  }

  click(x: number, y: number): ClickResult {
    if (x < 0 || x >= this.width || y < 0 || y >= this.height) {
      return "safe";
    }

    if (this.first_click) {
      this.placeMines(x, y);
      this.first_click = false;
    }

    const cell = this.board[y][x];
    if (cell.is_revealed || cell.is_flagged) {
      return "safe";
    }

    if (cell.is_mine) {
      cell.is_exploded = true;
      for (const row of this.board) {
        for (const c of row) {
          if (c.is_mine && !c.is_flagged) {
            c.is_revealed = true;
          }
        }
      }
      return "lost";
    }

    this.reveal(x, y);
    return this.checkWin() ? "win" : "safe";
  }

  toggleFlag(x: number, y: number): void {
    if (x < 0 || x >= this.width || y < 0 || y >= this.height) {
      return;
    }
    const cell = this.board[y][x];
    if (cell.is_revealed) {
      return;
    }
    cell.is_flagged = !cell.is_flagged;
  }

  isWon(): boolean {
    return this.checkWin();
  }

  isLost(): boolean {
    for (const row of this.board) {
      for (const c of row) {
        if (c.is_exploded) return true;
      }
    }
    return false;
  }

  reset(): void {
    this.board = [];
    this.mines_placed = false;
    this.first_click = true;
    this.revealed_count = 0;
  }

  getBoard(): BoardCell[][] {
    if (!this.board.length) {
      return Array.from({ length: this.height }, () =>
        Array.from({ length: this.width }, stubCell),
      );
    }
    const lost = this.isLost();
    return this.board.map((row) =>
      row.map((cell) => ({
        is_mine: cell.is_revealed || lost ? cell.is_mine : false,
        is_revealed: cell.is_revealed,
        is_flagged: cell.is_flagged,
        adjacent_mines: cell.is_revealed ? cell.adjacent_mines : 0,
        is_exploded: cell.is_exploded,
      })),
    );
  }

  getFlaggedCount(): number {
    if (!this.board.length) return 0;
    let count = 0;
    for (const row of this.board) {
      for (const c of row) {
        if (c.is_flagged) count += 1;
      }
    }
    return count;
  }

  private placeMines(safeX: number, safeY: number): void {
    this.board = Array.from({ length: this.height }, () =>
      Array.from({ length: this.width }, (): Cell => ({
        is_mine: false,
        is_revealed: false,
        is_flagged: false,
        adjacent_mines: 0,
        is_exploded: false,
      })),
    );

    const safeZone = new Set<string>([`${safeX},${safeY}`]);
    for (let dx = -1; dx <= 1; dx += 1) {
      for (let dy = -1; dy <= 1; dy += 1) {
        const nx = safeX + dx;
        const ny = safeY + dy;
        if (nx >= 0 && nx < this.width && ny >= 0 && ny < this.height) {
          safeZone.add(`${nx},${ny}`);
        }
      }
    }

    let positions: [number, number][] = [];
    for (let y = 0; y < this.height; y += 1) {
      for (let x = 0; x < this.width; x += 1) {
        if (!safeZone.has(`${x},${y}`)) {
          positions.push([x, y]);
        }
      }
    }

    if (positions.length < this.mine_count) {
      positions = [];
      for (let y = 0; y < this.height; y += 1) {
        for (let x = 0; x < this.width; x += 1) {
          if (x !== safeX || y !== safeY) {
            positions.push([x, y]);
          }
        }
      }
    }

    const shuffled = [...positions];
    for (let i = shuffled.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    for (const [mx, my] of shuffled.slice(0, this.mine_count)) {
      this.board[my][mx].is_mine = true;
    }

    for (let y = 0; y < this.height; y += 1) {
      for (let x = 0; x < this.width; x += 1) {
        if (this.board[y][x].is_mine) continue;
        let count = 0;
        for (let dx = -1; dx <= 1; dx += 1) {
          for (let dy = -1; dy <= 1; dy += 1) {
            const nx = x + dx;
            const ny = y + dy;
            if (
              nx >= 0 &&
              nx < this.width &&
              ny >= 0 &&
              ny < this.height &&
              this.board[ny][nx].is_mine
            ) {
              count += 1;
            }
          }
        }
        this.board[y][x].adjacent_mines = count;
      }
    }

    this.mines_placed = true;
  }

  private reveal(x: number, y: number): void {
    const cell = this.board[y][x];
    if (cell.is_revealed || cell.is_flagged || cell.is_mine) {
      return;
    }
    cell.is_revealed = true;
    this.revealed_count += 1;
    if (cell.adjacent_mines === 0) {
      for (let dx = -1; dx <= 1; dx += 1) {
        for (let dy = -1; dy <= 1; dy += 1) {
          const nx = x + dx;
          const ny = y + dy;
          if (nx >= 0 && nx < this.width && ny >= 0 && ny < this.height) {
            this.reveal(nx, ny);
          }
        }
      }
    }
  }

  private checkWin(): boolean {
    if (!this.mines_placed) return false;

    const total = this.width * this.height;
    if (this.revealed_count >= total - this.mine_count) {
      return true;
    }

    let flaggedMines = 0;
    let flaggedSafe = 0;
    for (const row of this.board) {
      for (const c of row) {
        if (!c.is_flagged) continue;
        if (c.is_mine) flaggedMines += 1;
        else flaggedSafe += 1;
      }
    }
    return flaggedMines === this.mine_count && flaggedSafe === 0;
  }
}
