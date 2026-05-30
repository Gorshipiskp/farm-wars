<script lang="ts">
  import WarehouseProductRow from "./WarehouseProductRow.svelte";
  import DropBin from "$components/shared/DropBin.svelte";
  import {
    selectSellProduct,
    sendSellAmount,
    sendSellProduct,
    syncSellSelection,
  } from "$lib/actions/gameActions";
  import { isSellableProduct } from "$lib/game/inventory";
  import { warehouseItemsGrouped, warehouseTotals } from "$lib/game/warehouse";
  import type { DragPayload } from "$lib/dnd/types";
  import { activeDrag } from "$lib/stores/drag";
  import type { PlayerState } from "$lib/api/types";
  import { selectedSellProductId } from "$lib/stores/matchUi";
  import { catalog } from "$lib/stores/session";

  interface Props {
    player: PlayerState | null;
    matchFinished: boolean;
  }

  let { player, matchFinished }: Props = $props();

  const groups = $derived(warehouseItemsGrouped(player, $catalog));
  const flat = $derived(groups.flatMap((g) => g.items));
  const totals = $derived(warehouseTotals(flat));
  const empty = $derived(flat.length === 0);

  $effect(() => {
    syncSellSelection(player);
  });

  async function onSellDrop(payload: DragPayload) {
    if (payload.kind !== "harvest") return;
    if (!isSellableProduct(payload.productId, $catalog)) return;
    await sendSellProduct(payload.productId);
  }
</script>

<section class="warehouse">
  <header class="wh-head">
    <h3>Склад</h3>
    {#if !empty}
      <span class="wh-stats" title="Позиции и оценка продажи">
        <span class="stat">{totals.kinds} видов</span>
        <span class="dot">·</span>
        <span class="stat">{totals.units} шт.</span>
        {#if totals.sellValue > 0}
          <span class="dot">·</span>
          <span class="stat value">≈{totals.sellValue} B</span>
        {/if}
      </span>
    {/if}
  </header>

  <DropBin
    label="Рынок"
    hint="Перетащи урожай сюда, чтобы продать"
    disabled={matchFinished}
    accept={(p) => p.kind === "harvest" && isSellableProduct(p.productId, $catalog)}
    onDrop={onSellDrop}
  />

  {#if empty}
    <div class="empty-state">
      <span class="empty-ico" aria-hidden="true">🧺</span>
      <p class="empty-title">Склад пуст</p>
      <p class="empty-hint">Собери урожай на грядках и продукцию животных в загоне</p>
    </div>
  {:else}
    {#each groups as group}
      <div class="wh-group">
        <h4 class="group-title">{group.label}</h4>
        <div class="wh-list">
          {#each group.items as item}
            <WarehouseProductRow
              productId={item.product_id}
              amount={item.amount}
              sellable={item.sellable}
              unitPrice={item.sellPrice}
              {matchFinished}
              selected={$selectedSellProductId === item.product_id}
              onSelect={() => selectSellProduct(item.product_id)}
              onSell={(n) => sendSellAmount(item.product_id, n)}
            />
          {/each}
        </div>
      </div>
    {/each}
  {/if}
</section>

<style>
  .warehouse {
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
  }

  .wh-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  h3 {
    margin: 0;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-soft);
  }

  .wh-stats {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.2rem;
    padding: 0.22rem 0.5rem;
    border-radius: 999px;
    background: linear-gradient(180deg, #fffef8, #ebe4d4);
    border: 1px solid #ddd0b8;
    font-size: 0.68rem;
    font-weight: 600;
    color: #6a5840;
  }

  .stat.value {
    color: #3d7a28;
    font-weight: 800;
  }

  .dot {
    opacity: 0.45;
  }

  .wh-group {
    padding: 0.55rem;
    border-radius: 12px;
    background: linear-gradient(180deg, #fffef8, #f5edd8);
    border: 1px solid #ddd0b8;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
  }

  .group-title {
    margin: 0 0 0.45rem;
    font-size: 0.72rem;
    font-weight: 700;
    color: #6a5840;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  .wh-list {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .empty-state {
    text-align: center;
    padding: 1.25rem 0.75rem;
    border-radius: 12px;
    border: 1px dashed #ccc0a8;
    background: linear-gradient(180deg, #faf6ee, #f0e8dc);
  }

  .empty-ico {
    font-size: 2rem;
    line-height: 1;
    display: block;
    margin-bottom: 0.35rem;
  }

  .empty-title {
    margin: 0 0 0.25rem;
    font-size: 0.88rem;
    font-weight: 800;
    color: var(--panel-header);
  }

  .empty-hint {
    margin: 0;
    font-size: 0.72rem;
    color: var(--text-soft);
  }

  :global(.warehouse .bin) {
    border-radius: 14px;
    background: linear-gradient(180deg, #fff8ec, #f0e4cc);
    border-style: solid;
    border-color: #d4c4a0;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
  }

  :global(.warehouse .bin.ready) {
    border-color: #c8a848;
    background: linear-gradient(180deg, #fff5dc, #f5e8b8);
  }

  :global(.warehouse .bin.over) {
    border-color: #6a9a48;
    background: linear-gradient(180deg, #e8f4e0, #d4e8c8);
  }
</style>
