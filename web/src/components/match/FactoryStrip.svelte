<script lang="ts">
  import { factoryLabel, myFactories } from "$lib/game/factories";
  import { realSecondsForTicks } from "$lib/game/pacing";
  import { productLabel } from "$lib/game/labels";
  import { productEmoji } from "$lib/game/visuals";
  import { recipeById } from "$lib/actions/gameActions";
  import type { WorldState } from "$lib/api/types";

  interface Props {
    world: WorldState | null;
    playerId: string;
    variant?: "default" | "bar";
  }

  let { world, playerId, variant = "default" }: Props = $props();

  const all = $derived(myFactories(world, playerId));
  const busyList = $derived(all.filter((f) => f.active_recipe_id));
  const hasContent = $derived(all.length > 0);
</script>

{#if hasContent}
  {#if variant === "bar"}
    <div class="bar-wrap">
      {#if busyList.length}
        {#each busyList as f}
          {@const out =
            recipeById(f.active_recipe_id ?? "")?.output_product_id ??
            f.active_recipe_id}
          <span class="status busy">
            <span class="spin">🔥</span>
            {factoryLabel(f.factory_type)}:
            {productEmoji(out ?? "")}
            {productLabel(out ?? "")}
            · {Math.ceil(realSecondsForTicks(f.remaining_time_sec ?? 0))} с
          </span>
        {/each}
      {:else}
        <span class="status idle">🏭 Все заводы свободны</span>
      {/if}
      {#each all as f}
        {@const active = f.active_recipe_id}
        <span class="fac" class:active={!!active}>
          {factoryLabel(f.factory_type)}
          {#if active}
            · {productLabel(recipeById(active)?.output_product_id ?? active)}
          {:else}
            · свободен
          {/if}
        </span>
      {/each}
    </div>
  {:else}
    <div class="list">
      {#each all as f}
        {@const active = f.active_recipe_id}
        <div class="line" class:busy={!!active}>
          <span class="fac-name">{factoryLabel(f.factory_type)}</span>
          {#if active}
            <span class="fac-work">
              {productEmoji(recipeById(active)?.output_product_id ?? active)}
              {productLabel(recipeById(active)?.output_product_id ?? active)}
              · {Math.ceil(realSecondsForTicks(f.remaining_time_sec ?? 0))} с
            </span>
          {:else}
            <span class="fac-idle">свободен</span>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
{/if}

<style>
  .bar-wrap {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.4rem 0.65rem;
    padding: 0.45rem 0.65rem;
    background: linear-gradient(90deg, #f8f0e4, #f0e8dc);
    border-radius: 10px;
    border: 1px solid rgba(110, 88, 62, 0.25);
    font-size: 0.78rem;
  }

  .status {
    font-weight: 600;
    padding: 0.2rem 0.5rem;
    border-radius: 8px;
  }

  .status.busy {
    background: #fff5e8;
    color: #6b3a10;
    border: 1px solid rgba(205, 115, 47, 0.35);
  }

  .status.idle {
    color: var(--text-soft);
  }

  .spin {
    display: inline-block;
    animation: wiggle 0.8s ease-in-out infinite;
  }

  @keyframes wiggle {
    0%,
    100% {
      transform: rotate(-5deg);
    }
    50% {
      transform: rotate(5deg);
    }
  }

  .fac {
    color: var(--text-soft);
    padding: 0.15rem 0.4rem;
    background: rgba(255, 255, 255, 0.5);
    border-radius: 6px;
    font-size: 0.72rem;
  }

  .fac.active {
    color: var(--accent);
    font-weight: 600;
  }

  .list {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    font-size: 0.75rem;
    margin-bottom: 0.5rem;
  }

  .line {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
    padding: 0.35rem 0.5rem;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.45);
    border: 1px solid rgba(200, 190, 170, 0.5);
  }

  .line.busy {
    background: #fff5e8;
    border-color: rgba(205, 115, 47, 0.35);
  }

  .fac-name {
    font-weight: 700;
    color: var(--text-soft);
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .line.busy .fac-name {
    color: #8a5020;
  }

  .fac-work {
    color: #6b3a10;
    font-weight: 600;
  }

  .fac-idle {
    color: var(--text-soft);
  }
</style>
