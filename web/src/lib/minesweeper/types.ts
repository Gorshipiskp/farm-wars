export type ClickResult = "safe" | "win" | "lost";

export type BoardCell = {
  is_mine: boolean;
  is_revealed: boolean;
  is_flagged: boolean;
  adjacent_mines: number;
  is_exploded: boolean;
};

export type MinesweeperPreset = "easy" | "medium" | "hard";
