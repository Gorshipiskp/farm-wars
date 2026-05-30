<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import { get } from "svelte/store";
  import { api, parseServerBase } from "$lib/api/client";
  import { ApiError } from "$lib/api/errors";
  import { LOBBY_HEALTH_POLL_MS, LOBBY_POLL_MS } from "$lib/game/constants";
  import { enterMatch, hostStartMatch } from "$lib/match/lifecycle";
  import { awaitingMatchStart } from "$lib/stores/lobby";
  import { pushToast } from "$lib/stores/toasts";
  import {
    catalog,
    isHost,
    joinCode,
    matchId,
    myJoinCode,
    playerId,
    playerName,
    serverConnected,
    serverHost,
    serverPort,
    statusMessage,
  } from "$lib/stores/session";

  let roster = $state<{ player_id: string; display_name: string }[]>([]);
  let hostPlayerId = $state("");
  let busy = $state(false);
  let pollTimer: ReturnType<typeof setInterval> | null = null;
  let healthTimer: ReturnType<typeof setInterval> | null = null;
  let healthCheckInFlight = false;

  const inRoom = $derived(!!$matchId);
  const hostWaiting = $derived(!!$awaitingMatchStart && $isHost && inRoom);
  const guestWaiting = $derived(!!$awaitingMatchStart && !$isHost && inRoom);

  function healthStatusText(health: {
    engine?: string;
    shop_handler?: string;
  }): string {
    return `Сервер готов · ${health.engine ?? "engine"} · ${health.shop_handler ?? "shop"}`;
  }

  async function checkServerConnection(opts: { manual?: boolean } = {}) {
    const manual = opts.manual ?? false;
    if (healthCheckInFlight) return;
    healthCheckInFlight = true;
    if (manual) busy = true;

    const wasConnected = get(serverConnected);
    try {
      const base = parseServerBase(get(serverHost), get(serverPort));
      api.setBaseUrl(base);
      const health = await api.health();
      catalog.set(health.catalog ?? null);
      serverConnected.set(true);

      const detail = healthStatusText(health);
      const inRoomNow = !!get(matchId);
      if (manual || !wasConnected || !inRoomNow) {
        statusMessage.set(detail);
      }
      if (!manual && !wasConnected) {
        pushToast("Связь с сервером восстановлена", "ok");
      }
    } catch (e) {
      serverConnected.set(false);
      const msg = e instanceof ApiError ? e.message : String(e);
      const inRoomNow = !!get(matchId);
      if (manual || wasConnected || !inRoomNow) {
        statusMessage.set(msg);
      }
      if (!manual && wasConnected) {
        pushToast("Связь с сервером потеряна", "warn");
      }
    } finally {
      healthCheckInFlight = false;
      if (manual) busy = false;
    }
  }

  async function connect() {
    await checkServerConnection({ manual: true });
  }

  async function createMatch() {
    busy = true;
    try {
      const r = await api.createMatch($playerName);
      matchId.set(r.match_id);
      playerId.set("p1");
      myJoinCode.set(r.join_code);
      joinCode.set(r.join_code);
      isHost.set(true);
      awaitingMatchStart.set(true);
      statusMessage.set("Комната создана — отправь код друзьям");
      await refreshRoster();
    } catch (e) {
      statusMessage.set(e instanceof ApiError ? e.message : String(e));
    } finally {
      busy = false;
    }
  }

  async function joinMatch() {
    busy = true;
    try {
      const r = await api.joinMatch($joinCode.trim(), $playerName);
      matchId.set(r.match_id);
      playerId.set(r.player_id);
      isHost.set(false);
      awaitingMatchStart.set(true);
      statusMessage.set("Вы в комнате — ждём старт от хоста");
      await refreshRoster();
    } catch (e) {
      statusMessage.set(e instanceof ApiError ? e.message : String(e));
    } finally {
      busy = false;
    }
  }

  async function refreshRoster() {
    if (!$matchId) return;
    const r = await api.pollRoster($matchId);
    roster = r.players ?? [];
    hostPlayerId = r.host_player_id ?? "";
  }

  async function startMatch() {
    if (!$matchId) return;
    busy = true;
    try {
      await hostStartMatch($matchId);
    } catch (e) {
      statusMessage.set(e instanceof ApiError ? e.message : String(e));
    } finally {
      busy = false;
    }
  }

  async function pollLobby() {
    const mid = get(matchId);
    if (!mid) return;
    try {
      await refreshRoster();
    } catch {
      /* roster optional */
    }
    if (!get(awaitingMatchStart) || get(isHost)) return;
    try {
      const sync = await api.pollSync(mid, 0);
      if (sync.world_state) await enterMatch(sync);
    } catch (e) {
      if (e instanceof ApiError && e.code === "NO_SYNC") return;
    }
  }

  async function copyCode(code: string) {
    try {
      await navigator.clipboard.writeText(code);
      pushToast("Код скопирован", "ok");
    } catch {
      pushToast("Не удалось скопировать", "warn");
    }
  }

  function playerEmoji(id: string): string {
    const n = id.charCodeAt(id.length - 1) % 4;
    return ["🧑‍🌾", "👩‍🌾", "🧔‍🌾", "👨‍🌾"][n];
  }

  onMount(() => {
    void checkServerConnection();
    healthTimer = setInterval(
      () => void checkServerConnection(),
      LOBBY_HEALTH_POLL_MS,
    );
    pollTimer = setInterval(() => void pollLobby(), LOBBY_POLL_MS);
  });

  onDestroy(() => {
    if (pollTimer) clearInterval(pollTimer);
    if (healthTimer) clearInterval(healthTimer);
  });
</script>

<div class="lobby">
  <header class="hero">
    <div class="hero-deco" aria-hidden="true">
      <span>🌾</span><span>🐄</span><span>🍞</span>
    </div>
    <div class="hero-text">
      <h1>Farm Wars</h1>
      <p class="subtitle">Фермерские войны · браузерный клиент</p>
    </div>
    <div class="conn-pill" class:online={$serverConnected}>
      <span class="dot"></span>
      {$serverConnected ? "Сервер онлайн" : "Нет связи"}
    </div>
  </header>

  <div class="columns">
    <section class="card">
      <h2 class="card-title"><span class="ico">📡</span> Подключение</h2>
      <div class="field-row">
        <label class="field grow">
          <span class="label">Адрес сервера</span>
          <input bind:value={$serverHost} placeholder="127.0.0.1" autocomplete="off" />
        </label>
        <label class="field port">
          <span class="label">Порт</span>
          <input bind:value={$serverPort} placeholder="8765" inputmode="numeric" />
        </label>
      </div>
      <label class="field">
        <span class="label">Имя фермера</span>
        <input bind:value={$playerName} placeholder="Фермер" maxlength="32" />
      </label>
      <button
        type="button"
        class="btn block"
        class:outline={$serverConnected}
        onclick={connect}
        disabled={busy}
      >
        {busy ? "…" : $serverConnected ? "Переподключиться" : "Проверить связь"}
      </button>
    </section>

    <section class="card">
      <h2 class="card-title"><span class="ico">🚪</span> Комната</h2>
      <label class="field">
        <span class="label">Код приглашения</span>
        <input
          bind:value={$joinCode}
          placeholder="ABCD12"
          class="code-input"
          class:has-code={!!$joinCode.trim()}
        />
      </label>
      <div class="btn-row">
        <button
          type="button"
          class="btn primary"
          onclick={createMatch}
          disabled={busy || !$serverConnected}
        >
          Создать матч
        </button>
        <button
          type="button"
          class="btn"
          onclick={joinMatch}
          disabled={busy || !$serverConnected || !$joinCode.trim()}
        >
          Войти по коду
        </button>
      </div>
    </section>
  </div>

  <div class="status-bar" class:ok={$serverConnected} class:warn={!$serverConnected && !busy}>
    <span class="status-icon">{$serverConnected ? "✓" : "!"}</span>
    <span class="status-text">{$statusMessage}</span>
  </div>

  {#if $myJoinCode}
    <div class="invite card highlight">
      <div class="invite-head">
        <span class="invite-label">Код для друзей</span>
        <button
          type="button"
          class="btn tiny"
          onclick={() => copyCode($myJoinCode)}
          title="Скопировать"
        >
          Копировать
        </button>
      </div>
      <button
        type="button"
        class="code-display"
        onclick={() => copyCode($myJoinCode)}
        title="Нажми, чтобы скопировать"
      >
        {$myJoinCode}
      </button>
      <p class="invite-hint">Друзья вводят код во вкладке «Комната» → «Войти по коду»</p>
    </div>
  {/if}

  {#if hostWaiting}
    <div class="banner host">
      <span class="banner-ico">🎮</span>
      <div>
        <strong>Вы хост</strong>
        <p>Когда все соберутся — нажмите «Начать игру»</p>
      </div>
      <button type="button" class="btn primary large" onclick={startMatch} disabled={busy}>
        Начать игру
      </button>
    </div>
  {:else if guestWaiting}
    <div class="banner guest">
      <span class="banner-ico pulse">⏳</span>
      <div>
        <strong>Ожидаем хоста</strong>
        <p>Матч начнётся автоматически</p>
      </div>
    </div>
  {/if}

  {#if roster.length > 0}
    <section class="card roster-card">
      <div class="roster-head">
        <h2 class="card-title"><span class="ico">👥</span> В комнате</h2>
        <span class="count">{roster.length}</span>
      </div>
      <ul class="players">
        {#each roster as p (p.player_id)}
          <li
            class="player"
            class:you={p.player_id === $playerId}
            class:host={p.player_id === hostPlayerId}
          >
            <span class="avatar">{playerEmoji(p.player_id)}</span>
            <span class="pname">{p.display_name || p.player_id}</span>
            <span class="badges">
              {#if p.player_id === hostPlayerId}<span class="badge host">хост</span>{/if}
              {#if p.player_id === $playerId}<span class="badge you">вы</span>{/if}
            </span>
          </li>
        {/each}
      </ul>
      <button type="button" class="btn ghost" onclick={refreshRoster} disabled={busy}>
        Обновить список
      </button>
    </section>
  {/if}
</div>

<style>
  .lobby {
    max-width: 560px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .hero {
    position: relative;
    text-align: center;
    padding: 1.5rem 1rem 1.25rem;
    background: linear-gradient(165deg, #fff9ee 0%, #f5e8d0 55%, #e8d4b8 100%);
    border: 2px solid var(--panel-border);
    border-radius: 18px;
    box-shadow:
      0 10px 32px rgba(45, 35, 20, 0.12),
      inset 0 1px 0 rgba(255, 255, 255, 0.6);
    overflow: hidden;
  }

  .hero::before {
    content: "";
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 20% 0%, rgba(255, 220, 120, 0.35), transparent 50%),
      radial-gradient(circle at 80% 100%, rgba(118, 168, 108, 0.2), transparent 45%);
    pointer-events: none;
  }

  .hero-deco {
    display: flex;
    justify-content: center;
    gap: 0.75rem;
    font-size: 1.75rem;
    margin-bottom: 0.35rem;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
  }

  .hero-text {
    position: relative;
  }

  h1 {
    margin: 0;
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: var(--panel-header);
    text-shadow: 0 1px 0 rgba(255, 255, 255, 0.5);
  }

  .subtitle {
    margin: 0.25rem 0 0.75rem;
    font-size: 0.9rem;
    color: var(--text-soft);
  }

  .conn-pill {
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.85rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
    background: rgba(195, 65, 55, 0.12);
    color: var(--error);
    border: 1px solid rgba(195, 65, 55, 0.25);
  }

  .conn-pill.online {
    background: rgba(52, 135, 72, 0.12);
    color: var(--ok);
    border-color: rgba(52, 135, 72, 0.3);
  }

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
  }

  .conn-pill.online .dot {
    box-shadow: 0 0 6px var(--ok);
  }

  .columns {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
  }

  @media (min-width: 520px) {
    .columns {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.85rem;
    }
  }

  .card {
    background: var(--panel-bg);
    border: 2px solid var(--panel-border);
    border-radius: 14px;
    padding: 1rem 1.1rem;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  }

  .card.highlight {
    border-color: var(--accent);
    background: linear-gradient(180deg, #fffbf3, #faf3e4);
  }

  .card-title {
    margin: 0 0 0.85rem;
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--panel-header);
    display: flex;
    align-items: center;
    gap: 0.35rem;
  }

  .ico {
    font-size: 1.1rem;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    margin-bottom: 0.75rem;
  }

  .field.grow {
    flex: 1;
    min-width: 0;
  }

  .field-row {
    display: flex;
    gap: 0.6rem;
  }

  .field.port {
    width: 5.5rem;
    flex-shrink: 0;
  }

  .label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-soft);
  }

  input {
    padding: 0.55rem 0.7rem;
    border: 1px solid #c4b5a0;
    border-radius: 10px;
    background: #fff;
    color: var(--text);
    transition:
      border-color 0.15s,
      box-shadow 0.15s;
  }

  input:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(205, 115, 47, 0.2);
  }

  .code-input {
    font-family: ui-monospace, "Cascadia Code", monospace;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }

  .code-input.has-code {
    font-weight: 700;
    color: var(--panel-header);
  }

  .btn {
    padding: 0.5rem 1rem;
    border-radius: 10px;
    border: 1px solid var(--panel-border);
    background: linear-gradient(180deg, #f0e6d6, #e0d4c0);
    color: var(--text);
    font-weight: 600;
    font-size: 0.88rem;
    transition:
      transform 0.1s,
      box-shadow 0.15s,
      background 0.15s;
  }

  .btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
  }

  .btn:active:not(:disabled) {
    transform: translateY(0);
  }

  .btn:disabled {
    opacity: 0.45;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  .btn.primary {
    background: linear-gradient(180deg, #e08a42, #cd732f);
    color: var(--text-on-dark);
    border-color: #a06030;
  }

  .btn.primary:hover:not(:disabled) {
    background: linear-gradient(180deg, var(--accent-hover), #cd732f);
  }

  .btn.block {
    width: 100%;
  }

  .btn.outline {
    background: transparent;
    border-style: dashed;
  }

  .btn.ghost {
    width: 100%;
    margin-top: 0.5rem;
    background: transparent;
    font-weight: 500;
    color: var(--text-soft);
  }

  .btn.tiny {
    padding: 0.25rem 0.55rem;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .btn.large {
    padding: 0.65rem 1.25rem;
    font-size: 1rem;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .btn-row {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
  }

  .status-bar {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 0.65rem 0.9rem;
    border-radius: 12px;
    background: #f5efe6;
    border: 1px solid #e0d6c8;
    font-size: 0.85rem;
    line-height: 1.4;
  }

  .status-bar.ok {
    background: #e8f4ea;
    border-color: #b8d8be;
  }

  .status-bar.warn {
    background: #fff8e6;
    border-color: #e8d8a8;
  }

  .status-icon {
    flex-shrink: 0;
    width: 1.25rem;
    height: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    font-size: 0.7rem;
    font-weight: 700;
    background: rgba(0, 0, 0, 0.06);
  }

  .status-bar.ok .status-icon {
    background: var(--ok);
    color: white;
  }

  .invite-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .invite-label {
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-soft);
  }

  .code-display {
    display: block;
    width: 100%;
    padding: 0.75rem 1rem;
    font-family: ui-monospace, "Cascadia Code", monospace;
    font-size: 1.75rem;
    font-weight: 800;
    letter-spacing: 0.2em;
    text-align: center;
    color: var(--panel-header);
    background: #fff;
    border: 2px dashed var(--accent);
    border-radius: 12px;
    cursor: pointer;
    transition: background 0.15s;
  }

  .code-display:hover {
    background: #fffaf0;
  }

  .invite-hint {
    margin: 0.5rem 0 0;
    font-size: 0.78rem;
    color: var(--text-soft);
    text-align: center;
  }

  .banner {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    padding: 1rem 1.1rem;
    border-radius: 14px;
    border: 2px solid;
  }

  .banner.host {
    background: linear-gradient(90deg, #fff5e8, #faf0dc);
    border-color: var(--accent);
  }

  .banner.guest {
    background: linear-gradient(90deg, #eef4fa, #e8f0f8);
    border-color: #7a9ec4;
  }

  .banner p {
    margin: 0.15rem 0 0;
    font-size: 0.85rem;
    color: var(--text-soft);
  }

  .banner-ico {
    font-size: 2rem;
    flex-shrink: 0;
  }

  .banner-ico.pulse {
    animation: pulse-ico 1.5s ease-in-out infinite;
  }

  @keyframes pulse-ico {
    0%,
    100% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.65;
      transform: scale(0.95);
    }
  }

  .banner > div {
    flex: 1;
    min-width: 0;
  }

  .roster-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }

  .roster-head .card-title {
    margin: 0;
  }

  .count {
    font-size: 0.8rem;
    font-weight: 700;
    padding: 0.2rem 0.5rem;
    border-radius: 8px;
    background: #ebe3d6;
    color: var(--text-soft);
  }

  .players {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .player {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.5rem 0.65rem;
    border-radius: 10px;
    background: #f5efe6;
    border: 1px solid transparent;
  }

  .player.you {
    border-color: var(--accent);
    background: #fff8ee;
  }

  .player.host {
    box-shadow: inset 3px 0 0 var(--money);
  }

  .avatar {
    font-size: 1.35rem;
    line-height: 1;
  }

  .pname {
    flex: 1;
    font-weight: 600;
    font-size: 0.9rem;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .badges {
    display: flex;
    gap: 0.3rem;
    flex-shrink: 0;
  }

  .badge {
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    padding: 0.15rem 0.4rem;
    border-radius: 6px;
  }

  .badge.host {
    background: var(--money);
    color: #5a4010;
  }

  .badge.you {
    background: var(--accent);
    color: var(--text-on-dark);
  }
</style>
