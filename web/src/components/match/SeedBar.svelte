<script lang="ts">
  import DraggableChip from "$components/shared/DraggableChip.svelte";
  import { plantIds, seedProductIdForPlant } from "$lib/game/catalogData";
  import { inventoryAmount } from "$lib/game/inventory";
  import { seedLabelFromPlantId } from "$lib/game/labels";
  import { plantEmoji } from "$lib/game/visuals";
  import { selectPlant } from "$lib/actions/gameActions";
  import type { PlayerState } from "$lib/api/types";
  import { selectedPlantId } from "$lib/stores/matchUi";
  import { catalog } from "$lib/stores/session";

  interface Props {
    player: PlayerState | null;
    matchFinished: boolean;
  }

  let { player, matchFinished }: Props = $props();

  const plants = $derived(plantIds($catalog));
</script>

<div class="seed-bar" aria-label="Семена">
  <span class="seed-bar-title">🌱 Семена</span>
  <p class="seed-bar-hint">Перетащи на пустую грядку</p>
  <div class="seed-chips">
    {#each plants as pid, i}
      {@const seedPid = seedProductIdForPlant($catalog, pid)}
      {@const have = inventoryAmount(player, seedPid)}
      <DraggableChip
        payload={{ kind: "seed", plantId: pid }}
        emoji={plantEmoji(pid)}
        label={seedLabelFromPlantId(pid, $catalog)}
        sublabel={have > 0 ? `×${have}` : "—"}
        disabled={matchFinished || have < 1}
        active={$selectedPlantId === pid}
        draggable={have > 0}
        onclick={() => selectPlant(pid)}
        class="seed-chip"
      />
    {/each}
  </div>
</div>

<style>
  .seed-bar {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    padding: 0.65rem 0.75rem;
    background: linear-gradient(180deg, #fff9ef, #f3ead8);
    border: 2px solid #c8b898;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(60, 45, 20, 0.08);
  }

  .seed-bar-title {
    font-size: 0.82rem;
    font-weight: 800;
    color: var(--panel-header);
    letter-spacing: 0.02em;
  }

  .seed-bar-hint {
    margin: 0;
    font-size: 0.72rem;
    color: var(--text-soft);
  }

  .seed-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    justify-content: center;
  }

  .seed-chips :global(.seed-chip) {
    flex: 1 1 5.5rem;
    max-width: 7.5rem;
    min-width: 4.75rem;
  }

  .seed-chips :global(.chip) {
    padding: 0.45rem 0.5rem;
    text-align: center;
  }

  .seed-chips :global(.label) {
    font-size: 0.72rem;
  }
</style>
