<script lang="ts">
  import { Minesweeper } from "$lib/minesweeper/game";
  import type { BoardCell } from "$lib/minesweeper/types";

  interface Props {
    tileLabel?: string;
    onWin: () => void;
    onLoss: () => void;
    onClose: () => void;
  }

  const CELL_PX = 34;

  let { tileLabel = "грядка", onWin, onLoss, onClose }: Props = $props();

  const [w, h, mines] = Minesweeper.preset("easy");
  let game = $state(new Minesweeper(w, h, mines));
  let board = $state<BoardCell[][]>(game.getBoard());
  let showLoss = $state(false);
  let lossTimer: ReturnType<typeof setTimeout> | null = null;
  let lossReported = $state(false);

  const flagged = $derived(game.getFlaggedCount());

  function refresh(): void {
    board = game.getBoard();
  }

  function handleLeft(x: number, y: number): void {
    if (showLoss) return;
    const result = game.click(x, y);
    refresh();
    if (result === "win") {
      onWin();
      return;
    }
    if (result === "lost") {
      showLoss = true;
      if (!lossReported) {
        lossReported = true;
        onLoss();
      }
      if (lossTimer) clearTimeout(lossTimer);
      lossTimer = setTimeout(() => {
        game.reset();
        showLoss = false;
        lossReported = false;
        refresh();
        lossTimer = null;
      }, 1500);
    }
  }

  function handleRight(x: number, y: number): void {
    if (showLoss) return;
    game.toggleFlag(x, y);
    refresh();
    if (game.isWon()) {
      onWin();
    }
  }

  function onKeydown(e: KeyboardEvent): void {
    if (e.key === "Escape") {
      e.preventDefault();
      onClose();
      return;
    }
    if (e.key === "r" || e.key === "R") {
      e.preventDefault();
      game.reset();
      showLoss = false;
      lossReported = false;
      if (lossTimer) {
        clearTimeout(lossTimer);
        lossTimer = null;
      }
      refresh();
    }
  }

  function numberClass(n: number): string {
    if (n <= 0) return "";
    return `n${Math.min(n, 8)}`;
  }

  function cellLabel(cell: BoardCell): string {
    if (cell.is_flagged && !cell.is_revealed) return "🚩";
    if (!cell.is_revealed) return "";
    if (cell.is_exploded) return "💥";
    if (cell.is_mine) return "●";
    if (cell.adjacent_mines > 0) return String(cell.adjacent_mines);
    return "";
  }
</script>

<svelte:window onkeydown={onKeydown} />

<!-- svelte-ignore a11y_no_static_element_interactions a11y_interactive_supports_focus a11y_click_events_have_key_events -->
<div
  class="backdrop"
  role="dialog"
  aria-modal="true"
  aria-label="Разминирование"
  tabindex="-1"
  onclick={(e) => {
    if (e.target === e.currentTarget) onClose();
  }}
>
  <div class="panel">
    <header class="head">
      <div>
        <h2>Сапёр</h2>
        <p class="sub">Мина на {tileLabel}. Разминируй поле.</p>
      </div>
      <button type="button" class="close" onclick={onClose} aria-label="Закрыть">×</button>
    </header>

    <p class="stats">🚩 {flagged} / {mines} · ЛКМ — открыть · ПКМ — флаг · R — заново · Esc — выход</p>

    {#if showLoss}
      <p class="loss">Взрыв! Соседние грядки пострадали. Новая попытка…</p>
    {/if}

    <div
      class="grid"
      style="--cell: {CELL_PX}px; --cols: {game.width}"
      role="grid"
      aria-label="Поле сапёра"
    >
      {#each board as row, y (y)}
        {#each row as cell, x (`${y}-${x}`)}
          <button
            type="button"
            class="cell {numberClass(cell.adjacent_mines)}"
            class:revealed={cell.is_revealed}
            class:flagged={cell.is_flagged && !cell.is_revealed}
            class:mine={cell.is_mine && cell.is_revealed}
            class:exploded={cell.is_exploded}
            class:empty={cell.is_revealed && cell.adjacent_mines === 0}
            onclick={() => handleLeft(x, y)}
            oncontextmenu={(e) => {
              e.preventDefault();
              handleRight(x, y);
            }}
            aria-label="Клетка {x + 1},{y + 1}"
          >
            {cellLabel(cell)}
          </button>
        {/each}
      {/each}
    </div>
  </div>
</div>

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    z-index: 200;
    background: rgba(20, 28, 20, 0.72);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }

  .panel {
    background: var(--panel-bg);
    border: 3px solid var(--panel-border);
    border-radius: 14px;
    padding: 1rem 1.1rem 1.2rem;
    max-width: min(96vw, 520px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
  }

  .head {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 0.75rem;
    margin-bottom: 0.5rem;
  }

  h2 {
    margin: 0;
    font-size: 1.25rem;
    color: var(--panel-header);
  }

  .sub {
    margin: 0.2rem 0 0;
    font-size: 0.88rem;
    color: var(--text-soft);
  }

  .close {
    border: none;
    background: transparent;
    font-size: 1.6rem;
    line-height: 1;
    color: var(--text-soft);
    padding: 0 0.25rem;
  }

  .close:hover {
    color: var(--error);
  }

  .stats {
    margin: 0 0 0.65rem;
    font-size: 0.8rem;
    color: var(--text-soft);
  }

  .loss {
    margin: 0 0 0.5rem;
    color: var(--error);
    font-weight: 600;
    font-size: 0.9rem;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(var(--cols), var(--cell));
    gap: 2px;
    width: fit-content;
    margin: 0 auto;
    user-select: none;
    touch-action: manipulation;
  }

  .cell {
    box-sizing: border-box;
    width: var(--cell);
    height: var(--cell);
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.85rem;
    line-height: 1;
    background: #9aa3ad;
    border: 1px solid #6b7280;
    border-radius: 3px;
    color: #1a1a1a;
    cursor: pointer;
  }

  .cell.revealed {
    background: #e8e4d8;
    border-color: #c4bfb3;
    cursor: default;
  }

  .cell.revealed.empty {
    background: #f4f1e8;
  }

  .cell.flagged {
    background: #b8c0cc;
  }

  .cell.mine {
    background: #2a2a2a;
    color: #f5f5f5;
  }

  .cell.exploded {
    background: var(--error);
    color: #fff;
  }

  .cell.n1 {
    color: #1565c0;
  }
  .cell.n2 {
    color: #2e7d32;
  }
  .cell.n3 {
    color: #c62828;
  }
  .cell.n4 {
    color: #283593;
  }
  .cell.n5,
  .cell.n6,
  .cell.n7,
  .cell.n8 {
    color: #4a148c;
  }
</style>
