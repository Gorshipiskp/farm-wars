<script lang="ts">
  import DraggableChip from "$components/shared/DraggableChip.svelte";

  interface Props {
    matchFinished: boolean;
  }

  let { matchFinished }: Props = $props();
</script>

<div class="tool-bar" aria-label="Лейка">
  <DraggableChip
    payload={{ kind: "watering_can" }}
    emoji="🪣"
    label="Лейка"
    sublabel="перетащи ↓"
    disabled={matchFinished}
    draggable={!matchFinished}
    class="tool-chip"
  />
</div>

<style>
  .tool-bar {
    display: flex;
    justify-content: center;
    padding: 0.45rem 0.55rem;
    background: linear-gradient(180deg, #e8f4fc, #d4e8f8);
    border: 2px solid #8ab4d4;
    border-radius: 10px;
  }

  .tool-bar :global(.tool-chip) {
    min-width: 5.5rem;
  }
</style>
