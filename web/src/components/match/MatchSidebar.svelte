<script lang="ts">
  import ActionsPanel from "./ActionsPanel.svelte";
  import GoalProgress from "./GoalProgress.svelte";
  import ShopPanel from "./ShopPanel.svelte";
  import CraftPanel from "./CraftPanel.svelte";
  import WarehousePanel from "./WarehousePanel.svelte";
  import TabBar from "$components/shared/TabBar.svelte";
  import DraggableChip from "$components/shared/DraggableChip.svelte";
  import { sendSabotage } from "$lib/actions/gameActions";
  import { winProductId } from "$lib/game/catalogData";
  import { recipeHintForTarget } from "$lib/game/winGoal";
  import { inventoryAmount } from "$lib/game/inventory";
  import { activeDrag } from "$lib/stores/drag";
  import type { PlayerState, WorldState } from "$lib/api/types";
  import { catalog, playerId } from "$lib/stores/session";

  interface Props {
    player: PlayerState | null;
    world: WorldState | null;
    matchFinished: boolean;
    hasOpponentTiles: boolean;
  }

  let { player, world, matchFinished, hasOpponentTiles }: Props = $props();

  let sidebarTab = $state("play");

  const target = $derived(
    world?.win_condition?.target_product_id ?? winProductId($catalog),
  );
  const haveGoal = $derived(inventoryAmount(player, target));
  const sabotages = $derived($catalog?.sabotages ?? []);

  const recipeHint = $derived(recipeHintForTarget($catalog, target));

  const sidebarTabs = $derived([
    { id: "play", label: "Действия" },
    { id: "warehouse", label: "Склад" },
    { id: "shop", label: "Магазин" },
    { id: "craft", label: "Ремесло" },
    ...(hasOpponentTiles && sabotages.length ? [{ id: "pvp", label: "PvP" }] : []),
  ]);

  function onSidebarDragOver(e: DragEvent) {
    const drag = $activeDrag;
    if (drag?.kind === "harvest") {
      e.preventDefault();
    }
  }

</script>

<aside class="sidebar">
  <h2 class="title"><span class="title-ico">🎮</span> Панель матча</h2>

  <GoalProgress
    targetProductId={target}
    have={haveGoal}
    recipeHint={recipeHint}
  />

  <TabBar
    tabs={sidebarTabs}
    activeId={sidebarTab}
    onSelect={(id) => (sidebarTab = id)}
  />

  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="tab-body" role="presentation" ondragover={onSidebarDragOver}>
    {#if sidebarTab === "play"}
      <ActionsPanel {matchFinished} onOpenWarehouse={() => (sidebarTab = "warehouse")} />

    {:else if sidebarTab === "warehouse"}
      <WarehousePanel {player} {matchFinished} />

    {:else if sidebarTab === "shop"}
      <ShopPanel {player} {matchFinished} />

    {:else if sidebarTab === "craft"}
      <CraftPanel {player} {world} {matchFinished} />

    {:else if sidebarTab === "pvp"}
      <section>
        <h3>Саботаж</h3>
        <p class="muted">Перетащи тип саботажа на клетку соперника (вкладка «Соперники»)</p>
        <div class="chips">
          {#each sabotages as sab}
            {@const can = (player?.money_bestiki ?? 0) >= sab.price}
            <DraggableChip
              payload={{ kind: "sabotage", sabotageId: sab.sabotage_id }}
              label={sab.display_name ?? sab.sabotage_id}
              sublabel={`${sab.price} B`}
              disabled={matchFinished || !can}
              class="sab"
              onclick={() => sendSabotage(sab.sabotage_id)}
            />
          {/each}
        </div>
      </section>

    {/if}
  </div>
</aside>

<style>
  .sidebar {
    background: linear-gradient(180deg, #faf6ee, #f0e8dc);
    border: 2px solid var(--panel-border);
    border-radius: 16px;
    padding: 1rem 1.1rem;
    min-width: 280px;
    max-width: 380px;
    max-height: calc(100vh - 4rem);
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
  }

  .title {
    margin: 0;
    font-size: 1.05rem;
    font-weight: 800;
    color: var(--panel-header);
    display: flex;
    align-items: center;
    gap: 0.35rem;
  }

  .title-ico {
    font-size: 1.15rem;
  }

  .tab-body {
    overflow-y: auto;
    flex: 1;
    min-height: 0;
    padding-right: 0.25rem;
  }

  h3 {
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin: 0 0 0.5rem;
    color: var(--text-soft);
  }

  section {
    margin-bottom: 1rem;
  }

  .chips {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .chips :global(.sab) {
    background: #d4b0a0;
  }

  .muted {
    font-size: 0.8rem;
    color: var(--text-soft);
    margin: 0 0 0.5rem;
  }

</style>
