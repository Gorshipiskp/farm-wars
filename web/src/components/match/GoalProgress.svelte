<script lang="ts">
  import { productLabel } from "$lib/game/labels";
  import { productEmoji } from "$lib/game/visuals";

  interface Props {
    targetProductId: string;
    have: number;
    need?: number;
    recipeHint?: string | null;
  }

  let { targetProductId, have, need = 1, recipeHint = null }: Props = $props();

  const ratio = $derived(need > 0 ? Math.min(1, have / need) : 0);
  const done = $derived(have >= need);
  const emoji = $derived(productEmoji(targetProductId));
</script>

<div class="goal" class:done>
  <div class="head">
    <span class="title">
      <span class="ico" aria-hidden="true">{done ? "🏆" : "🎯"}</span>
      Цель — {productLabel(targetProductId)}
    </span>
    <span class="count">{have}/{need}</span>
  </div>
  <div class="bar" role="progressbar" aria-valuenow={have} aria-valuemax={need}>
    <div class="fill" style="width: {ratio * 100}%">
      <span class="bar-emoji">{emoji}</span>
    </div>
  </div>
  {#if recipeHint}
    <p class="recipe">{recipeHint}</p>
  {/if}
</div>

<style>
  .goal {
    padding: 0.75rem 0.85rem;
    background: linear-gradient(135deg, #fff9ee, #f5ebe0);
    border: 1px solid #e0d0b8;
    border-radius: 12px;
  }

  .goal.done {
    border-color: var(--ok);
    background: linear-gradient(135deg, #eef8f0, #e0f0e4);
  }

  .head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.45rem;
  }

  .title {
    font-weight: 700;
    font-size: 0.85rem;
    color: var(--panel-header);
    display: flex;
    align-items: center;
    gap: 0.35rem;
  }

  .ico {
    font-size: 1rem;
  }

  .count {
    font-weight: 800;
    font-size: 0.9rem;
    color: var(--accent);
    background: #fff;
    padding: 0.15rem 0.45rem;
    border-radius: 8px;
    border: 1px solid #e0d6c8;
  }

  .goal.done .count {
    color: var(--ok);
    border-color: #b8d8be;
  }

  .bar {
    height: 14px;
    background: #e0d6c8;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.08);
  }

  .fill {
    height: 100%;
    background: linear-gradient(90deg, #cd732f, #e08a42);
    border-radius: 8px;
    transition: width 0.35s ease;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-right: 4px;
    min-width: 0;
  }

  .goal.done .fill {
    background: linear-gradient(90deg, #2d7a3e, var(--ok));
  }

  .bar-emoji {
    font-size: 0.65rem;
    line-height: 1;
  }

  .recipe {
    margin: 0.4rem 0 0;
    font-size: 0.72rem;
    color: var(--text-soft);
    line-height: 1.35;
  }
</style>
