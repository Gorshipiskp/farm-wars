/** Действия матча по физическим клавишам (раскладка не влияет). */
export type MatchHotkeyAction =
  | "care"
  | "plant"
  | "harvest"
  | "recipe"
  | "buy_animal"
  | "sell"
  | "sabotage"
  | { seed: number };

const CODE_TO_ACTION: Record<string, MatchHotkeyAction> = {
  KeyW: "care",
  KeyF: "care",
  KeyT: "plant",
  KeyH: "harvest",
  KeyB: "recipe",
  KeyC: "buy_animal",
  KeyV: "sell",
  KeyX: "sabotage",
  Digit1: { seed: 0 },
  Digit2: { seed: 1 },
  Digit3: { seed: 2 },
  Digit4: { seed: 3 },
  Digit5: { seed: 4 },
  Digit6: { seed: 5 },
  Digit7: { seed: 6 },
  Digit8: { seed: 7 },
  Digit9: { seed: 8 },
};

/** Не перехватывать клавиши при вводе в форму (лобби и т.д.). */
export function shouldIgnoreGameHotkey(e: KeyboardEvent): boolean {
  const el = e.target;
  if (!(el instanceof HTMLElement)) return false;
  if (el.isContentEditable) return true;
  const tag = el.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
}

export function matchHotkeyFromEvent(e: KeyboardEvent): MatchHotkeyAction | null {
  if (e.altKey || e.ctrlKey || e.metaKey) return null;
  return CODE_TO_ACTION[e.code] ?? null;
}
