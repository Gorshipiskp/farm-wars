<script lang="ts">
  import { sendBuyProduct } from "$lib/actions/gameActions";
  import { shopItemsGrouped } from "$lib/game/shop";
  import { productLabel } from "$lib/game/labels";
  import { productEmoji } from "$lib/game/visuals";
  import type { PlayerState } from "$lib/api/types";
  import { catalog } from "$lib/stores/session";

  interface Props {
    player: PlayerState | null;
    matchFinished: boolean;
  }

  let { player, matchFinished }: Props = $props();

  const groups = $derived(shopItemsGrouped($catalog));
  const money = $derived(player?.money_bestiki ?? 0);
</script>

<section class="shop">
  <header class="shop-head">
    <h3>Магазин</h3>
    <span class="wallet" title="Бестики">
      <span class="coin">🪙</span>
      <strong>{money}</strong> B
    </span>
  </header>
  <p class="shop-hint">Нажми на товар, чтобы купить</p>

  {#each groups as group}
    <div class="shop-group">
      <h4 class="group-title">{group.label}</h4>
      <div class="shop-grid">
        {#each group.items as item}
          {@const can = money >= item.price}
          <button
            type="button"
            class="shop-card"
            class:affordable={can}
            class:expensive={!can}
            disabled={matchFinished || !can}
            onclick={() => sendBuyProduct(item.product_id)}
          >
            <span class="card-emoji" aria-hidden="true">{productEmoji(item.product_id)}</span>
            <span class="card-body">
              <span class="card-name">{productLabel(item.product_id)}</span>
              <span class="card-price">{item.price} B</span>
            </span>
          </button>
        {/each}
      </div>
    </div>
  {:else}
    <p class="muted">В каталоге нет товаров</p>
  {/each}
</section>

<style>
  .shop {
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
  }

  .shop-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }

  h3 {
    margin: 0;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-soft);
  }

  .wallet {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.55rem;
    border-radius: 999px;
    background: linear-gradient(180deg, #fff8dc, #f0e0a8);
    border: 1px solid #c8a848;
    font-size: 0.78rem;
    color: #5a4020;
  }

  .wallet strong {
    font-weight: 800;
  }

  .coin {
    font-size: 0.9rem;
    line-height: 1;
  }

  .shop-hint {
    margin: 0;
    font-size: 0.72rem;
    color: var(--text-soft);
  }

  .shop-group {
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

  .shop-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0.35rem;
  }

  .shop-card {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.5rem 0.6rem;
    border-radius: 10px;
    border: 1px solid #d8ccb4;
    background: linear-gradient(180deg, #fff, #f3ebe0);
    text-align: left;
    transition:
      transform 0.1s,
      box-shadow 0.12s,
      border-color 0.12s;
  }

  .shop-card.affordable:hover:not(:disabled) {
    transform: translateY(-1px);
    border-color: #8ab86a;
    box-shadow: 0 3px 10px rgba(60, 90, 40, 0.12);
  }

  .shop-card.expensive {
    opacity: 0.55;
  }

  .shop-card:disabled {
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  .card-emoji {
    font-size: 1.5rem;
    line-height: 1;
    flex-shrink: 0;
    width: 2rem;
    text-align: center;
  }

  .card-body {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
    min-width: 0;
    flex: 1;
  }

  .card-name {
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--text);
  }

  .card-price {
    font-size: 0.72rem;
    font-weight: 600;
    color: #6a5020;
  }

  .shop-card.affordable .card-price {
    color: #3d7a28;
  }

  .muted {
    font-size: 0.8rem;
    color: var(--text-soft);
    margin: 0;
  }
</style>
