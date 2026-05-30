<script lang="ts">
  import FactoryStrip from "./FactoryStrip.svelte";
  import { recipeById, selectRecipe, sendRecipe, sendRecipeFor } from "$lib/actions/gameActions";
  import {
    canCraftRecipe,
    recipeCookLabel,
    recipeIngredientStatus,
    recipeOutputProductId,
    recipeSellUnitPrice,
  } from "$lib/game/craft";
  import { factoryLabel, myFactoryTypes } from "$lib/game/factories";
  import { productLabel } from "$lib/game/labels";
  import { productEmoji } from "$lib/game/visuals";
  import type { CatalogRecipe, PlayerState, WorldState } from "$lib/api/types";
  import { selectedRecipeId } from "$lib/stores/matchUi";
  import { catalog, playerId } from "$lib/stores/session";

  interface Props {
    player: PlayerState | null;
    world: WorldState | null;
    matchFinished: boolean;
  }

  let { player, world, matchFinished }: Props = $props();

  const recipes = $derived($catalog?.recipes ?? []);
  const factoryTypes = $derived(myFactoryTypes(world, $playerId));
  const craftRecipe = $derived(recipeById($selectedRecipeId));

  const recipesByBuilding = $derived.by(() => {
    const map = new Map<string, CatalogRecipe[]>();
    for (const r of recipes) {
      const key = r.building_type;
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(r);
    }
    return [...map.entries()].map(([building, list]) => ({
      building,
      label: factoryLabel(building),
      recipes: list,
    }));
  });

  function statusFor(recipe: CatalogRecipe) {
    return recipeIngredientStatus(player, recipe);
  }
</script>

<section class="craft">
  <header class="craft-head">
    <h3>Ремесло</h3>
    <button
      type="button"
      class="bake-btn"
      disabled={matchFinished || !craftRecipe || !canCraftRecipe(player, craftRecipe).ok}
      onclick={() => sendRecipe()}
    >
      🔥 Печь <kbd>B</kbd>
    </button>
  </header>
  <p class="craft-hint">
    Выбери рецепт — ингредиенты с галочкой есть в сумке.
    {#if craftRecipe}
      Продажа готового: <strong>{recipeSellUnitPrice(craftRecipe, $catalog)} B</strong> за шт.
    {/if}
  </p>

  {#if recipes.length && factoryTypes.size > 0}
    {#each recipesByBuilding as group}
      {@const hasFactory = factoryTypes.has(group.building)}
      <div class="craft-group" class:locked={!hasFactory}>
        <h4 class="group-title">
          <span class="group-ico">🏭</span>
          {group.label}
          {#if !hasFactory}
            <span class="lock">нет завода</span>
          {/if}
        </h4>
        <div class="recipe-list">
          {#each group.recipes as r}
            {@const ings = statusFor(r)}
            {@const canCraft = canCraftRecipe(player, r).ok}
            {@const hasFactory = factoryTypes.has(r.building_type)}
            {@const outId = recipeOutputProductId(r)}
            {@const sellB = recipeSellUnitPrice(r, $catalog)}
            <div
              class="recipe-row"
              class:active={$selectedRecipeId === r.recipe_id}
              class:ready={canCraft && hasFactory}
              class:disabled={matchFinished || !hasFactory}
            >
              <button
                type="button"
                class="recipe-card"
                disabled={matchFinished || !hasFactory}
                onclick={() => selectRecipe(r.recipe_id)}
              >
                <span class="recipe-out">
                  <span class="out-emoji">{productEmoji(outId)}</span>
                  <span class="out-text">
                    <span class="out-name">{productLabel(outId)}</span>
                    <span class="recipe-meta">
                      <span class="meta-pill cook-time" title="Длительность готовки">
                        ⏱ {recipeCookLabel(r)}
                      </span>
                      {#if sellB > 0}
                        <span class="meta-pill sell-price" title="Цена продажи на рынке (1 шт.)">
                          🏪 {sellB} B
                        </span>
                      {/if}
                    </span>
                  </span>
                </span>
                <ul class="reqs">
                  {#each ings as ing}
                    <li class:ok={ing.ok} class:lack={!ing.ok}>
                      <span class="mark" aria-hidden="true">{ing.ok ? "✓" : "✗"}</span>
                      <span class="req-text">{ing.label} ×{ing.need}</span>
                      <span class="req-have">{ing.have}/{ing.need}</span>
                    </li>
                  {:else}
                    <li class="muted-req">Без ингредиентов</li>
                  {/each}
                </ul>
              </button>
              <button
                type="button"
                class="start-btn"
                title="Запустить на этом заводе"
                disabled={matchFinished || !hasFactory || !canCraft}
                onclick={() => sendRecipeFor(r.recipe_id)}
              >
                ▶
              </button>
            </div>
          {/each}
        </div>
      </div>
    {/each}
  {:else}
    <p class="muted">Нет рецептов или заводов</p>
  {/if}

  <div class="factories">
    <h4 class="group-title">Статус заводов</h4>
    <FactoryStrip {world} playerId={$playerId} />
  </div>
</section>

<style>
  .craft {
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
  }

  .craft-head {
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

  .bake-btn {
    padding: 0.3rem 0.55rem;
    border-radius: 8px;
    border: 1px solid #a06030;
    background: linear-gradient(180deg, #e08a42, #cd732f);
    color: var(--text-on-dark);
    font-size: 0.72rem;
    font-weight: 700;
    white-space: nowrap;
  }

  .bake-btn:disabled {
    opacity: 0.45;
    filter: grayscale(0.3);
  }

  .craft-hint {
    margin: 0;
    font-size: 0.72rem;
    color: var(--text-soft);
  }

  .craft-group {
    padding: 0.55rem;
    border-radius: 12px;
    background: linear-gradient(180deg, #fff9f0, #f3e8d8);
    border: 1px solid #ddd0b8;
  }

  .craft-group.locked {
    opacity: 0.65;
  }

  .group-title {
    margin: 0 0 0.45rem;
    display: flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.72rem;
    font-weight: 700;
    color: #6a5840;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .group-ico {
    font-size: 0.85rem;
  }

  .lock {
    margin-left: auto;
    font-size: 0.65rem;
    font-weight: 600;
    color: #a05040;
    text-transform: none;
    letter-spacing: 0;
  }

  .recipe-list {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .recipe-row {
    display: flex;
    align-items: stretch;
    gap: 0.3rem;
    border-radius: 10px;
    border: 1px solid #d8ccb4;
    background: linear-gradient(180deg, #fff, #f5efe6);
    overflow: hidden;
    transition: box-shadow 0.12s;
  }

  .recipe-row.active {
    border-color: #a06030;
    box-shadow: 0 0 0 2px rgba(205, 115, 47, 0.35);
  }

  .recipe-row.ready.active {
    border-color: #4a8a38;
  }

  .recipe-row.disabled {
    opacity: 0.55;
  }

  .recipe-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    padding: 0.5rem 0.55rem;
    border: none;
    background: transparent;
    text-align: left;
    min-width: 0;
  }

  .recipe-card:disabled {
    cursor: not-allowed;
  }

  .recipe-out {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    min-width: 0;
  }

  .start-btn {
    flex-shrink: 0;
    width: 2.1rem;
    border: none;
    border-left: 1px solid #d8ccb4;
    background: linear-gradient(180deg, #e08a42, #cd732f);
    color: #fff;
    font-size: 0.7rem;
    cursor: pointer;
  }

  .start-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .out-emoji {
    font-size: 1.25rem;
    line-height: 1;
  }

  .out-text {
    display: flex;
    flex-direction: column;
    gap: 0.12rem;
    min-width: 0;
  }

  .out-name {
    font-size: 0.82rem;
    font-weight: 800;
    color: var(--text);
    line-height: 1.2;
  }

  .recipe-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
  }

  .meta-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.15rem;
    width: fit-content;
    padding: 0.1rem 0.4rem;
    border-radius: 999px;
    font-size: 0.65rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }

  .meta-pill.cook-time {
    color: #5a4828;
    background: linear-gradient(180deg, #fff8ec, #f0e4cc);
    border: 1px solid #d4c4a0;
  }

  .meta-pill.sell-price {
    color: #1a4a20;
    background: linear-gradient(180deg, #e8f8e0, #c8e8b0);
    border: 1px solid #6a9a48;
  }

  .craft-hint strong {
    color: #2d6a32;
    font-weight: 800;
  }

  .reqs {
    margin: 0;
    padding: 0;
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
  }

  .reqs li {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.7rem;
    line-height: 1.3;
  }

  .reqs li.ok {
    color: #2d6a32;
  }

  .reqs li.lack {
    color: #8a4038;
  }

  .mark {
    width: 0.85rem;
    font-weight: 800;
    flex-shrink: 0;
  }

  .req-text {
    flex: 1;
    min-width: 0;
  }

  .req-have {
    font-size: 0.65rem;
    opacity: 0.85;
    font-variant-numeric: tabular-nums;
  }

  .muted-req,
  .muted {
    font-size: 0.75rem;
    color: var(--text-soft);
  }

  .factories {
    padding-top: 0.25rem;
  }

  kbd {
    font-size: 0.65rem;
    opacity: 0.85;
  }
</style>
