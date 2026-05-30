<script lang="ts">
  import { productLabel } from "$lib/game/labels";
  import { productEmoji } from "$lib/game/visuals";

  interface Props {
    winnerId: string;
    myPlayerId: string;
    targetProductId: string;
  }

  let { winnerId, myPlayerId, targetProductId }: Props = $props();

  const won = $derived(winnerId === myPlayerId);
  const emoji = $derived(productEmoji(targetProductId));
</script>

<div class="overlay" role="dialog" aria-modal="true" aria-labelledby="win-title">
  <div class="box" class:won>
    <div class="deco" aria-hidden="true">{won ? "🎉" : "🌾"}</div>
    <h2 id="win-title">{won ? "Победа!" : "Матч окончен"}</h2>
    {#if won}
      <p class="sub">Первым на ферме</p>
      <p class="prize">
        <span class="prize-emoji">{emoji}</span>
        <strong>{productLabel(targetProductId)}</strong>
      </p>
    {:else}
      <p class="sub">Победитель</p>
      <p class="prize loser"><strong>{winnerId}</strong></p>
    {/if}
  </div>
</div>

<style>
  .overlay {
    position: fixed;
    inset: 0;
    z-index: 200;
    background: rgba(25, 35, 25, 0.82);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    animation: fade-in 0.3s ease;
  }

  @keyframes fade-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  .box {
    background: linear-gradient(165deg, #fff9ee, #f5e8d0);
    border: 4px solid var(--accent);
    border-radius: 24px;
    padding: 2rem 2.5rem;
    max-width: 400px;
    width: 100%;
    text-align: center;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
    animation: pop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  }

  @keyframes pop {
    from {
      transform: scale(0.85);
      opacity: 0;
    }
    to {
      transform: scale(1);
      opacity: 1;
    }
  }

  .box.won {
    border-color: var(--ok);
    background: linear-gradient(165deg, #f0faf2, #e0f0e4);
  }

  .deco {
    font-size: 3rem;
    margin-bottom: 0.5rem;
  }

  h2 {
    margin: 0 0 0.5rem;
    font-size: 2rem;
    font-weight: 800;
    color: var(--panel-header);
  }

  .box.won h2 {
    color: var(--ok);
  }

  .sub {
    margin: 0;
    font-size: 0.9rem;
    color: var(--text-soft);
  }

  .prize {
    margin: 0.75rem 0 0;
    font-size: 1.15rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.35rem;
  }

  .prize-emoji {
    font-size: 2.5rem;
  }

  .prize.loser strong {
    font-size: 1.35rem;
    color: var(--panel-header);
  }
</style>
