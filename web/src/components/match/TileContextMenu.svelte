<script lang="ts">
  import { onMount } from "svelte";
  import {
    sendBuyAnimal,
    sendCare,
    sendHarvestOnTile,
    sendPlant,
    sendSabotageOnTile,
  } from "$lib/actions/gameActions";
  import { buildTileContextMenu, type ContextMenuItem } from "$lib/game/contextMenu";
  import { findTile } from "$lib/game/tiles";
  import { closeContextMenu, contextMenu } from "$lib/stores/contextMenu";
  import { matchFinished, selectedTileId, worldState } from "$lib/stores/game";
  import { catalog, playerId } from "$lib/stores/session";

  let openSubmenu = $state<string | null>(null);

  const state = $derived($contextMenu);
  const tile = $derived(
    state ? findTile($worldState, state.tileId) : null,
  );
  const items = $derived(
    tile && state
      ? buildTileContextMenu(
          tile,
          $playerId,
          $matchFinished,
          $catalog?.sabotages ?? [],
        )
      : [],
  );

  async function runAction(id: string) {
    if (!state || !tile) return;
    const tid = state.tileId;
    selectedTileId.set(tid);
    closeContextMenu();

    if (id === "select") return;
    if (id === "care") await sendCare();
    else if (id === "plant") await sendPlant();
    else if (id === "harvest") await sendHarvestOnTile(tid);
    else if (id === "buy_animal") await sendBuyAnimal();
    else if (id.startsWith("sabotage:")) {
      await sendSabotageOnTile(tid, id.slice("sabotage:".length));
    }
  }

  function onDocClick() {
    closeContextMenu();
    openSubmenu = null;
  }

  function onDocKey(e: KeyboardEvent) {
    if (e.key === "Escape") closeContextMenu();
  }

  onMount(() => {
    document.addEventListener("click", onDocClick);
    document.addEventListener("keydown", onDocKey);
    return () => {
      document.removeEventListener("click", onDocClick);
      document.removeEventListener("keydown", onDocKey);
    };
  });

  function menuStyle(s: { x: number; y: number }): string {
    const pad = 8;
    const maxX = typeof window !== "undefined" ? window.innerWidth - 200 : s.x;
    const maxY = typeof window !== "undefined" ? window.innerHeight - 280 : s.y;
    const left = Math.min(s.x, maxX - pad);
    const top = Math.min(s.y, maxY - pad);
    return `left:${left}px;top:${top}px`;
  }
</script>

{#if state && tile && items.length}
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
  <div
    class="menu"
    style={menuStyle(state)}
    role="menu"
    tabindex="-1"
    onclick={(e) => e.stopPropagation()}
  >
    {#each items as item (item.id)}
      {#if item.children?.length}
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div
          class="sub-wrap"
          role="presentation"
          onmouseenter={() => (openSubmenu = item.id)}
          onmouseleave={() => (openSubmenu = null)}
        >
          <button type="button" class="item" class:danger={item.danger}>
            {item.label} ▸
          </button>
          {#if openSubmenu === item.id}
            <div class="sub" role="menu">
              {#each item.children as child (child.id)}
                <button
                  type="button"
                  class="item"
                  class:danger={child.danger}
                  disabled={child.disabled}
                  onclick={() => runAction(child.id)}
                >
                  {child.label}
                </button>
              {/each}
            </div>
          {/if}
        </div>
      {:else}
        <button
          type="button"
          class="item"
          class:danger={item.danger}
          disabled={item.disabled}
          onclick={() => runAction(item.id)}
        >
          {item.label}
          {#if item.hotkey}
            <kbd>{item.hotkey}</kbd>
          {/if}
        </button>
      {/if}
    {/each}
  </div>
{/if}

<style>
  .menu {
    position: fixed;
    z-index: 300;
    min-width: 180px;
    background: var(--panel-bg);
    border: 2px solid var(--panel-border);
    border-radius: 10px;
    padding: 0.35rem 0;
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.25);
  }

  .item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 0.45rem 0.85rem;
    border: none;
    background: transparent;
    font-size: 0.88rem;
    text-align: left;
    cursor: pointer;
    color: var(--text);
  }

  .item:hover:not(:disabled) {
    background: #ebe3d6;
  }

  .item.danger {
    color: var(--error);
  }

  .item:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  kbd {
    font-size: 0.7rem;
    color: var(--text-soft);
    margin-left: 0.5rem;
  }

  .sub-wrap {
    position: relative;
  }

  .sub {
    position: absolute;
    left: 100%;
    top: 0;
    min-width: 160px;
    background: var(--panel-bg);
    border: 2px solid var(--panel-border);
    border-radius: 10px;
    padding: 0.35rem 0;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
  }
</style>
