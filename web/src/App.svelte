<script lang="ts">
  import LobbyPanel from "$components/lobby/LobbyPanel.svelte";
  import MatchView from "$components/match/MatchView.svelte";
  import ToastStack from "$components/match/ToastStack.svelte";
  import { screen } from "$lib/stores/session";
</script>

<main class="shell" class:centered={$screen === "lobby"}>
  {#if $screen === "lobby"}
    <LobbyPanel />
    <ToastStack />
  {:else}
    <MatchView />
  {/if}
</main>

<style>
  .shell {
    max-width: 1400px;
    margin: 0 auto;
    padding: 1rem 1rem 1.5rem;
    min-height: 100vh;
  }

  .shell.centered {
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
</style>
