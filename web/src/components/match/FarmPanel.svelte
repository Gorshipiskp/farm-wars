<script lang="ts">

  import FarmGrid from "./FarmGrid.svelte";

  import HotkeyBar from "./HotkeyBar.svelte";

  import SeedBar from "./SeedBar.svelte";

  import WateringCanBar from "./WateringCanBar.svelte";

  import AnimalBar from "./AnimalBar.svelte";

  import TabBar from "$components/shared/TabBar.svelte";

  import { FARM_COLS, FARM_PEN_COLS } from "$lib/game/constants";

  import type { PlayerState, WorldState } from "$lib/api/types";

  import {

    animalTilesForOwner,

    opponentDisplayName,

    opponents,

    plantTilesForOwner,

  } from "$lib/game/tiles";

  import { viewOpponentId } from "$lib/stores/matchUi";

  import { playerId } from "$lib/stores/session";

  import { canHarvestPlant, isRipeTile } from "$lib/game/visuals";



  interface Props {

    world: WorldState | null;

    player: PlayerState | null;

    selectedTileId: string | null;

    matchFinished: boolean;

    hint: string;

    onSelectTile: (tileId: string) => void;

  }



  let { world, player, selectedTileId, matchFinished, hint, onSelectTile }: Props = $props();



  let farmTab = $state<"mine" | "enemy">("mine");



  const myPlantTiles = $derived(plantTilesForOwner(world, $playerId));

  const myAnimalTiles = $derived(animalTilesForOwner(world, $playerId));

  const harvestReadyCount = $derived(
    myPlantTiles.filter((t) => canHarvestPlant(t)).length,
  );

  const ripeNeedsWaterCount = $derived(
    myPlantTiles.filter((t) => isRipeTile(t) && !canHarvestPlant(t)).length,
  );

  const opps = $derived(opponents(world, $playerId));

  const oppPlantTiles = $derived(

    $viewOpponentId ? plantTilesForOwner(world, $viewOpponentId) : [],

  );

  const oppAnimalTiles = $derived(

    $viewOpponentId ? animalTilesForOwner(world, $viewOpponentId) : [],

  );

  const oppName = $derived(opponentDisplayName(world, $playerId, $viewOpponentId));



  const farmTabs = $derived([

    { id: "mine", label: "🌾 Моя ферма" },

    ...(opps.length

      ? [{ id: "enemy", label: opps.length > 1 ? "⚔️ Соперники" : `⚔️ ${oppName}` }]

      : []),

  ]);



  const oppSubTabs = $derived(

    opps.map((p) => ({

      id: p.player_id,

      label: (p.display_name || p.player_id).slice(0, 14),

    })),

  );



  $effect(() => {

    if (opps.length && !$viewOpponentId) {

      viewOpponentId.set(opps[0].player_id);

    }

    if (!opps.length && farmTab === "enemy") farmTab = "mine";

  });

</script>



<article class="farm-card">

  <div class="farm-head">

    {#if farmTabs.length > 1}

      <TabBar

        tabs={farmTabs}

        activeId={farmTab}

        onSelect={(id) => (farmTab = id as "mine" | "enemy")}

      />

    {:else}

      <h2 class="solo-title">🌾 Твоя ферма</h2>

    {/if}

  </div>



  <p class="hint">

    <span class="hint-ico">💡</span>

    {hint}

  </p>

  {#if farmTab === "mine" && (harvestReadyCount > 0 || ripeNeedsWaterCount > 0)}
    <div class="ripe-banner" role="status">
      {#if harvestReadyCount > 0}
        <span class="ripe-banner-item ready">
          🧺 {harvestReadyCount}
          {harvestReadyCount === 1 ? "грядка" : harvestReadyCount < 5 ? "грядки" : "грядок"}
          готовы — <kbd>H</kbd>
        </span>
      {/if}
      {#if ripeNeedsWaterCount > 0}
        <span class="ripe-banner-item dry">
          💧 {ripeNeedsWaterCount} созрели, но нужен полив перед сбором
        </span>
      {/if}
    </div>
  {/if}

  {#if farmTab === "mine"}

    <section class="zone garden-zone">

      <h3 class="zone-title">🌱 Огород</h3>

      <SeedBar {player} {matchFinished} />

      <WateringCanBar {matchFinished} />

      <div class="field-wrap garden">

        <FarmGrid

          tiles={myPlantTiles}

          {selectedTileId}

          own={true}

          myPlayerId={$playerId}

          {player}

          {world}

          {matchFinished}

          cols={world?.map?.width ?? FARM_COLS}

          splashPlantTiles={myPlantTiles}

          ariaLabel="Огород"

          onSelect={onSelectTile}

        />

      </div>

    </section>



    <section class="zone pen-zone">

      <h3 class="zone-title">🐄 Загон</h3>

      <AnimalBar {player} {matchFinished} />

      <div class="field-wrap pen">

        <FarmGrid

          tiles={myAnimalTiles}

          {selectedTileId}

          own={true}

          myPlayerId={$playerId}

          {player}

          {world}

          {matchFinished}

          cols={FARM_PEN_COLS}

          ariaLabel="Загон"

          onSelect={onSelectTile}

        />

      </div>

    </section>

  {:else if oppPlantTiles.length || oppAnimalTiles.length}

    {#if oppSubTabs.length > 1}

      <TabBar

        tabs={oppSubTabs}

        activeId={$viewOpponentId ?? ""}

        onSelect={(id) => viewOpponentId.set(id)}

        compact

      />

    {/if}

    <p class="opp-banner">

      <span>Ферма соперника</span>

      <strong>{oppName}</strong>

    </p>



    {#if oppPlantTiles.length}

      <section class="zone garden-zone enemy-view">

        <h3 class="zone-title">Огород</h3>

        <div class="field-wrap garden enemy-view">

          <FarmGrid

            tiles={oppPlantTiles}

            {selectedTileId}

            own={false}

            myPlayerId={$playerId}

            {player}

            {world}

            {matchFinished}

            cols={world?.map?.width ?? FARM_COLS}

            ariaLabel="Огород соперника"

            onSelect={onSelectTile}

          />

        </div>

      </section>

    {/if}



    {#if oppAnimalTiles.length}

      <section class="zone pen-zone enemy-view">

        <h3 class="zone-title">Загон</h3>

        <div class="field-wrap pen enemy-view">

          <FarmGrid

            tiles={oppAnimalTiles}

            {selectedTileId}

            own={false}

            myPlayerId={$playerId}

            {player}

            {world}

            {matchFinished}

            cols={FARM_PEN_COLS}

            ariaLabel="Загон соперника"

            onSelect={onSelectTile}

          />

        </div>

      </section>

    {/if}

  {/if}



  <HotkeyBar disabled={matchFinished} />

</article>



<style>

  .farm-card {

    flex: 1;

    min-width: 280px;

    display: flex;

    flex-direction: column;

    gap: 0.85rem;

    padding: 1rem 1.1rem;

    background: linear-gradient(165deg, #f8f4ea 0%, #ebe3d4 100%);

    border: 2px solid var(--panel-border);

    border-radius: 16px;

    box-shadow:

      0 6px 24px rgba(45, 35, 20, 0.1),

      inset 0 1px 0 rgba(255, 255, 255, 0.5);

  }



  .farm-head {

    min-height: 2.25rem;

  }



  .solo-title {

    margin: 0;

    font-size: 1rem;

    font-weight: 700;

    color: var(--panel-header);

  }



  .hint {

    margin: 0;

    display: flex;

    gap: 0.5rem;

    align-items: flex-start;

    font-size: 0.82rem;

    color: var(--text);

    line-height: 1.4;

    padding: 0.6rem 0.75rem;

    background: #fff;

    border-radius: 10px;

    border: 1px solid #e0d6c8;

    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);

  }



  .hint-ico {

    flex-shrink: 0;

    font-size: 1rem;

  }

  .ripe-banner {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    padding: 0.5rem 0.65rem;
    border-radius: 10px;
    border: 2px solid #6ac85a;
    background: linear-gradient(180deg, #e8f8e0, #d0f0c0);
    box-shadow: 0 2px 8px rgba(52, 135, 72, 0.15);
  }

  .ripe-banner-item {
    font-size: 0.78rem;
    font-weight: 700;
    line-height: 1.35;
  }

  .ripe-banner-item.ready {
    color: #1a4a20;
  }

  .ripe-banner-item.dry {
    color: #6a4018;
    font-weight: 600;
  }

  .ripe-banner kbd {
    display: inline-flex;
    padding: 0.08rem 0.35rem;
    font-size: 0.68rem;
    font-weight: 800;
    background: #fff;
    border: 1px solid #6a9a48;
    border-radius: 4px;
  }

  .zone {

    display: flex;

    flex-direction: column;

    gap: 0.5rem;

  }



  .zone-title {

    margin: 0;

    font-size: 0.88rem;

    font-weight: 800;

    color: var(--panel-header);

    letter-spacing: 0.02em;

  }



  .field-wrap {

    padding: 0.85rem;

    border-radius: 14px;

    border: 2px solid;

    box-shadow: inset 0 2px 12px rgba(0, 0, 0, 0.12);

    display: flex;

    flex-direction: column;

    align-items: center;

  }



  .field-wrap.garden {

    background: linear-gradient(180deg, #8fbc6a 0%, #6a9e4a 100%);

    border-color: #4a7a32;

  }



  .field-wrap.pen {

    background: linear-gradient(180deg, #c4a882 0%, #a08058 100%);

    border-color: #6a5038;

  }



  .field-wrap.enemy-view,

  .zone.enemy-view .field-wrap.garden {

    background: linear-gradient(180deg, #a08070 0%, #806050 100%);

    border-color: #5a4030;

  }



  .zone.enemy-view .field-wrap.pen {

    background: linear-gradient(180deg, #907868 0%, #705848 100%);

    border-color: #504030;

  }



  .opp-banner {

    margin: 0;

    width: 100%;

    text-align: center;

    font-size: 0.8rem;

    color: var(--text-soft);

    display: flex;

    flex-direction: column;

    gap: 0.1rem;

  }



  .opp-banner strong {

    font-size: 0.95rem;

    color: var(--text);

  }

</style>

