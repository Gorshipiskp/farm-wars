<script lang="ts">
  import DraggableChip from "$components/shared/DraggableChip.svelte";
  import { selectAnimal } from "$lib/actions/gameActions";
  import { animalLabel } from "$lib/game/labels";
  import { animalEmoji } from "$lib/game/visuals";
  import type { PlayerState } from "$lib/api/types";
  import { selectedAnimalId } from "$lib/stores/matchUi";
  import { catalog } from "$lib/stores/session";

  interface Props {
    player: PlayerState | null;
    matchFinished: boolean;
  }

  let { player, matchFinished }: Props = $props();

  const animals = $derived($catalog?.animals ?? []);
</script>

<div class="animal-bar" aria-label="Животные">
  <span class="animal-bar-title">🐄 Животные</span>
  <p class="animal-bar-hint">Перетащи на пустой загон · уход (W) списывает Bestiki</p>
  <div class="animal-chips">
    {#each animals as a}
      {@const can = (player?.money_bestiki ?? 0) >= a.price}
      <DraggableChip
        payload={{ kind: "animal", animalId: a.animal_id }}
        emoji={animalEmoji(a.animal_id)}
        label={animalLabel(a.animal_id)}
        sublabel={`${a.price} B`}
        disabled={matchFinished || !can}
        draggable={!matchFinished && can}
        active={$selectedAnimalId === a.animal_id}
        onclick={() => selectAnimal(a.animal_id)}
        class="animal-chip"
      />
    {/each}
  </div>
</div>

<style>
  .animal-bar {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    padding: 0.65rem 0.75rem;
    background: linear-gradient(180deg, #f5efe6, #e8dcc8);
    border: 2px solid #b8a080;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(60, 45, 20, 0.08);
  }

  .animal-bar-title {
    font-size: 0.82rem;
    font-weight: 800;
    color: var(--panel-header);
  }

  .animal-bar-hint {
    margin: 0;
    font-size: 0.72rem;
    color: var(--text-soft);
  }

  .animal-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    justify-content: center;
  }

  .animal-chips :global(.animal-chip) {
    flex: 1 1 5.5rem;
    max-width: 7.5rem;
    min-width: 4.75rem;
  }

</style>
