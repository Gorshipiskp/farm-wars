<script lang="ts">
  import DraggableChip from "$components/shared/DraggableChip.svelte";
  import { productLabel } from "$lib/game/labels";
  import { productEmoji } from "$lib/game/visuals";
  import type { DragPayload } from "$lib/dnd/types";

  interface Props {
    productId: string;
    amount: number;
    sellable: boolean;
    unitPrice?: number;
    matchFinished: boolean;
    selected: boolean;
    onSelect: () => void;
    onSell: (amount: number) => void;
  }

  let {
    productId,
    amount,
    sellable,
    unitPrice = 0,
    matchFinished,
    selected,
    onSelect,
    onSell,
  }: Props = $props();

  const payload = $derived<DragPayload>({ kind: "harvest", productId });
  const lineTotal = $derived(sellable && unitPrice > 0 ? unitPrice * amount : 0);
</script>

<article class="row" class:not-sellable={!sellable} class:selected>
  <div class="main">
    <DraggableChip
      {payload}
      emoji={productEmoji(productId)}
      label={productLabel(productId)}
      sublabel={sellable ? `×${amount}` : `×${amount} · не продаётся`}
      disabled={matchFinished || !sellable}
      draggable={sellable}
      active={selected}
      onclick={onSelect}
    />
    {#if sellable && unitPrice > 0}
      <span class="price-meta">
        <span class="unit">{unitPrice} B/шт.</span>
        {#if amount > 1}
          <span class="total">≈{lineTotal} B</span>
        {/if}
      </span>
    {/if}
  </div>

  {#if sellable}
    <div class="sell-row">
      <button
        type="button"
        class="sell-btn"
        disabled={matchFinished || amount < 1}
        onclick={() => onSell(1)}
      >
        −1
      </button>
      <button
        type="button"
        class="sell-btn"
        disabled={matchFinished || amount < 5}
        onclick={() => onSell(5)}
      >
        −5
      </button>
      <button
        type="button"
        class="sell-btn sell-all"
        disabled={matchFinished || amount < 1}
        onclick={() => onSell(amount)}
        title="Продать всё"
      >
        Всё
      </button>
    </div>
  {/if}
</article>

<style>
  .row {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    padding: 0.45rem;
    border-radius: 10px;
    border: 1px solid #e0d6c4;
    background: linear-gradient(180deg, #fff, #f8f2e8);
    transition:
      border-color 0.12s,
      box-shadow 0.12s;
  }

  .row.selected {
    border-color: #c8a848;
    box-shadow: 0 0 0 2px rgba(200, 168, 72, 0.25);
  }

  .row.not-sellable {
    opacity: 0.85;
    background: linear-gradient(180deg, #f8f6f2, #eeeae4);
  }

  .main {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0;
    border: none;
    background: transparent;
    text-align: left;
    cursor: pointer;
  }

  .main:disabled {
    cursor: not-allowed;
  }

  .main :global(.chip) {
    flex: 1;
    min-width: 0;
  }

  .price-meta {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.05rem;
    flex-shrink: 0;
    font-size: 0.68rem;
    font-weight: 700;
    color: #6a5020;
  }

  .total {
    color: #3d7a28;
    font-size: 0.72rem;
  }

  .sell-row {
    display: grid;
    grid-template-columns: 1fr 1fr 1.2fr;
    gap: 0.3rem;
  }

  .sell-btn {
    padding: 0.35rem 0.25rem;
    border-radius: 8px;
    border: 1px solid var(--panel-border);
    background: linear-gradient(180deg, #fff, #ebe3d6);
    font-size: 0.72rem;
    font-weight: 800;
    color: var(--text);
    transition: transform 0.1s, box-shadow 0.12s;
  }

  .sell-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  }

  .sell-btn:disabled {
    opacity: 0.4;
    transform: none;
    box-shadow: none;
  }

  .sell-all {
    background: linear-gradient(180deg, #e8c878, #d4a84a);
    border-color: #a08030;
    color: #3a2a10;
  }
</style>
