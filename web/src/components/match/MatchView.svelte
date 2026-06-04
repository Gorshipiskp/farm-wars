<script lang="ts">
  import FarmPanel from "./FarmPanel.svelte";
  import MatchHeader from "./MatchHeader.svelte";
  import MatchSidebar from "./MatchSidebar.svelte";
  import ToastStack from "./ToastStack.svelte";
  import TileContextMenu from "./TileContextMenu.svelte";
  import WateringCanDragFollower from "./WateringCanDragFollower.svelte";
  import WinOverlay from "./WinOverlay.svelte";
  import MinesweeperModal from "./MinesweeperModal.svelte";
  import { get } from "svelte/store";
  import { activeDrag, dragPointer } from "$lib/stores/drag";
  import {
    selectPlant,
    sendBuyAnimal,
    sendCare,
    sendHarvest,
    sendPlant,
    sendRecipe,
    sendSell,
    sendClearMine,
    sendMinesweeperLost,
    sendSabotage,
  } from "$lib/actions/gameActions";
  import { plantIds, winProductId } from "$lib/game/catalogData";
  import { tileHint } from "$lib/game/labels";
  import { findTile, opponents, tilesForOwner } from "$lib/game/tiles";
  import { matchHotkeyFromEvent, shouldIgnoreGameHotkey } from "$lib/input/hotkeys";
  import { leaveMatch } from "$lib/match/lifecycle";
  import { matchFinished, selectedTileId, worldState } from "$lib/stores/game";
  import { selectedPlantId, viewOpponentId } from "$lib/stores/matchUi";
  import { catalog, playerId } from "$lib/stores/session";

  const myPlayer = $derived(
    $worldState?.players?.find((p) => p.player_id === $playerId) ?? null,
  );

  const selectedTile = $derived(findTile($worldState, $selectedTileId));
  const hint = $derived(tileHint(selectedTile, $selectedPlantId, $playerId, $catalog));

  const winnerId = $derived($worldState?.win_condition?.winner_player_id);
  const tickId = $derived($worldState?.tick_id ?? 0);
  const targetProduct = $derived(
    $worldState?.win_condition?.target_product_id ?? winProductId($catalog),
  );

  const plantList = $derived(plantIds($catalog));
  const oppTiles = $derived(
    $viewOpponentId ? tilesForOwner($worldState, $viewOpponentId) : [],
  );
  const hasOpponents = $derived(opponents($worldState, $playerId).length > 0);

  let defuseTileId = $state<string | null>(null);
  const defuseTile = $derived(findTile($worldState, defuseTileId));

  function onKeydown(e: KeyboardEvent) {
    if (defuseTileId) return;
    if ($matchFinished || shouldIgnoreGameHotkey(e)) return;
    const action = matchHotkeyFromEvent(e);
    if (!action) return;

    e.preventDefault();

    if (action === "care") void sendCare();
    else if (action === "plant") void sendPlant();
    else if (action === "harvest") void sendHarvest();
    else if (action === "recipe") void sendRecipe();
    else if (action === "buy_animal") void sendBuyAnimal();
    else if (action === "sell") void sendSell();
    else if (action === "sabotage") {
      const sab = $catalog?.sabotages?.[0]?.sabotage_id ?? "poison_water";
      void sendSabotage(sab);
    }
    else if ("seed" in action && action.seed < plantList.length) {
      selectPlant(plantList[action.seed]);
    }
  }

  function onSelectTile(tileId: string) {
    const tile = findTile($worldState, tileId);
    if (
      tile &&
      $playerId &&
      tile.owner_player_id === $playerId &&
      (tile.flags ?? []).includes("MINED")
    ) {
      defuseTileId = tileId;
      selectedTileId.set(tileId);
      return;
    }
    selectedTileId.set(tileId);
  }

  function closeMinesweeper(): void {
    defuseTileId = null;
  }

  async function onMinesweeperWin(): Promise<void> {
    const tileId = defuseTileId;
    defuseTileId = null;
    if (!tileId) return;
    await sendClearMine(tileId);
  }

  async function onMinesweeperLoss(): Promise<void> {
    const tileId = defuseTileId;
    if (!tileId) return;
    await sendMinesweeperLost(tileId);
  }

  function onWindowDragOver(e: DragEvent) {
    if (get(activeDrag)?.kind !== "watering_can") return;
    e.preventDefault();
    dragPointer.set({ x: e.clientX, y: e.clientY });
  }
</script>

<svelte:window
  onkeydown={onKeydown}
  ondragover={onWindowDragOver}
  ondragend={() => dragPointer.set(null)}
/>

<div class="match">
  <section class="match-panel">
    <MatchHeader
      player={myPlayer}
      world={$worldState}
      {tickId}
      matchFinished={$matchFinished}
      onLeave={leaveMatch}
    />

    <div class="match-body">
      <FarmPanel
        world={$worldState}
        player={myPlayer}
        selectedTileId={$selectedTileId}
        matchFinished={$matchFinished}
        {hint}
        onSelectTile={onSelectTile}
      />

      <MatchSidebar
        player={myPlayer}
        world={$worldState}
        matchFinished={$matchFinished}
        hasOpponentTiles={hasOpponents && oppTiles.length > 0}
      />
    </div>
  </section>
</div>

{#if defuseTileId}
  <MinesweeperModal
    tileLabel={defuseTile?.tile_id ?? "грядка"}
    onWin={() => void onMinesweeperWin()}
    onLoss={() => void onMinesweeperLoss()}
    onClose={closeMinesweeper}
  />
{/if}

{#if $matchFinished && winnerId}
  <WinOverlay
    winnerId={winnerId}
    myPlayerId={$playerId}
    targetProductId={targetProduct}
    onLeave={leaveMatch}
  />
{/if}

<WateringCanDragFollower />
<TileContextMenu />
<ToastStack />

<style>
  .match {
    width: 100%;
  }

  .match-panel {
    background: var(--panel-bg);
    border: 2px solid var(--panel-border);
    border-radius: 18px;
    padding: 1.15rem 1.25rem 1.25rem;
    box-shadow:
      0 12px 40px rgba(30, 25, 15, 0.15),
      inset 0 1px 0 rgba(255, 255, 255, 0.6);
  }

  .match-body {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
    margin-top: 0.85rem;
    align-items: start;
  }

  @media (min-width: 900px) {
    .match-body {
      grid-template-columns: 1fr minmax(300px, 380px);
    }
  }
</style>
