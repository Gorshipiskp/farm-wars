<script lang="ts">
  import {
    sendBuyAnimal,
    sendCare,
    sendHarvest,
    sendPlant,
    sendRecipe,
    sendSell,
  } from "$lib/actions/gameActions";

  interface ActionDef {
    id: string;
    emoji: string;
    label: string;
    hint: string;
    key: string;
    tone: "water" | "grow" | "harvest" | "fire" | "animal" | "market";
    run: () => void;
  }

  interface ActionGroup {
    title: string;
    subtitle?: string;
    actions: ActionDef[];
  }

  interface Props {
    matchFinished: boolean;
    onOpenWarehouse?: () => void;
  }

  let { matchFinished, onOpenWarehouse }: Props = $props();

  const groups: ActionGroup[] = [
    {
      title: "Уход",
      subtitle: "Выбери клетку на ферме",
      actions: [
        {
          id: "care",
          emoji: "💧",
          label: "Уход",
          hint: "Полив грядки или корм в загоне",
          key: "W",
          tone: "water",
          run: () => void sendCare(),
        },
      ],
    },
    {
      title: "Грядки",
      actions: [
        {
          id: "plant",
          emoji: "🌱",
          label: "Посадить",
          hint: "Семена с панели слева",
          key: "T",
          tone: "grow",
          run: () => void sendPlant(),
        },
        {
          id: "harvest",
          emoji: "🧺",
          label: "Собрать",
          hint: "Урожай с созревшей грядки",
          key: "H",
          tone: "harvest",
          run: () => void sendHarvest(),
        },
      ],
    },
    {
      title: "Производство",
      actions: [
        {
          id: "recipe",
          emoji: "🔥",
          label: "Печь",
          hint: "Рецепт на вкладке «Ремесло»",
          key: "B",
          tone: "fire",
          run: () => void sendRecipe(),
        },
        {
          id: "animal",
          emoji: "🐄",
          label: "Животное",
          hint: "Купить в выбранный загон",
          key: "C",
          tone: "animal",
          run: () => void sendBuyAnimal(),
        },
      ],
    },
    {
      title: "Рынок",
      actions: [
        {
          id: "sell",
          emoji: "🏪",
          label: "Продать",
          hint: "Быстрая продажа со склада",
          key: "V",
          tone: "market",
          run: () => void sendSell(),
        },
      ],
    },
  ];
</script>

<section class="actions-panel" aria-label="Действия на ферме">
  <header class="panel-head">
    <div>
      <h3>Действия</h3>
      <p class="panel-lead">Клетка на ферме → кнопка или клавиша</p>
    </div>
    <span class="panel-badge" title="Горячие клавиши">⌨</span>
  </header>

  {#each groups as group}
    <div class="action-group">
      <div class="group-head">
        <span class="group-title">{group.title}</span>
        {#if group.subtitle}
          <span class="group-sub">{group.subtitle}</span>
        {/if}
      </div>
      <div class="action-list" class:single={group.actions.length === 1}>
        {#each group.actions as action (action.id)}
          <button
            type="button"
            class="action-card tone-{action.tone}"
            disabled={matchFinished}
            onclick={action.run}
          >
            <span class="icon-wrap" aria-hidden="true">{action.emoji}</span>
            <span class="card-body">
              <span class="card-label">{action.label}</span>
              <span class="card-hint">{action.hint}</span>
            </span>
            <kbd class="card-key">{action.key}</kbd>
          </button>
        {/each}
      </div>
    </div>
  {/each}

  <footer class="panel-foot">
    <p class="foot-tip">
      Урожай, цены и перетаскивание —
      {#if onOpenWarehouse}
        <button type="button" class="link-btn" onclick={onOpenWarehouse}>вкладка «Склад»</button>
      {:else}
        вкладка «Склад»
      {/if}
    </p>
    <p class="foot-tip secondary">ПКМ по клетке — контекстное меню · <kbd>1–6</kbd> выбор семян</p>
  </footer>
</section>

<style>
  .actions-panel {
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
  }

  .panel-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.5rem;
    padding: 0.55rem 0.65rem;
    border-radius: 12px;
    background: linear-gradient(135deg, #fffef8 0%, #f0e6d0 100%);
    border: 1px solid #ddd0b8;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
  }

  h3 {
    margin: 0;
    font-size: 0.82rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--panel-header);
  }

  .panel-lead {
    margin: 0.2rem 0 0;
    font-size: 0.72rem;
    color: var(--text-soft);
    line-height: 1.35;
  }

  .panel-badge {
    flex-shrink: 0;
    width: 2rem;
    height: 2rem;
    display: grid;
    place-items: center;
    border-radius: 10px;
    background: linear-gradient(180deg, #ebe3d6, #d8ccb4);
    border: 1px solid #c4b5a0;
    font-size: 1rem;
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.6);
  }

  .action-group {
    padding: 0.5rem 0.55rem 0.55rem;
    border-radius: 12px;
    background: linear-gradient(180deg, #fffef8, #f5edd8);
    border: 1px solid #ddd0b8;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
  }

  .group-head {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0.35rem 0.5rem;
    margin-bottom: 0.45rem;
    padding-bottom: 0.35rem;
    border-bottom: 1px solid rgba(110, 88, 62, 0.12);
  }

  .group-title {
    font-size: 0.7rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #6a5840;
  }

  .group-sub {
    font-size: 0.68rem;
    color: var(--text-soft);
  }

  .action-list {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.4rem;
  }

  .action-list.single {
    grid-template-columns: 1fr;
  }

  .action-card {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.5rem 0.55rem;
    border-radius: 11px;
    border: 1px solid rgba(110, 88, 62, 0.22);
    background: linear-gradient(180deg, #fff 0%, #f3ebe0 100%);
    text-align: left;
    transition:
      transform 0.12s ease,
      box-shadow 0.12s ease,
      border-color 0.12s ease;
    box-shadow:
      0 1px 0 rgba(255, 255, 255, 0.9) inset,
      0 2px 6px rgba(60, 45, 30, 0.06);
  }

  .action-card:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow:
      0 1px 0 rgba(255, 255, 255, 0.9) inset,
      0 6px 14px rgba(60, 45, 30, 0.12);
  }

  .action-card:active:not(:disabled) {
    transform: translateY(0);
  }

  .action-card:disabled {
    opacity: 0.42;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  .icon-wrap {
    flex-shrink: 0;
    width: 2.15rem;
    height: 2.15rem;
    display: grid;
    place-items: center;
    border-radius: 10px;
    font-size: 1.15rem;
    line-height: 1;
    border: 1px solid rgba(0, 0, 0, 0.06);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.5);
  }

  .tone-water .icon-wrap {
    background: linear-gradient(145deg, #d4eef8, #8ec8e8);
  }

  .tone-grow .icon-wrap {
    background: linear-gradient(145deg, #d8f0c8, #8bc96a);
  }

  .tone-harvest .icon-wrap {
    background: linear-gradient(145deg, #ffe8b8, #e8b85a);
  }

  .tone-fire .icon-wrap {
    background: linear-gradient(145deg, #ffd4b0, #e88a48);
  }

  .tone-animal .icon-wrap {
    background: linear-gradient(145deg, #e8dcc8, #b89870);
  }

  .tone-market .icon-wrap {
    background: linear-gradient(145deg, #fff0a8, #e8c040);
  }

  .tone-water:hover:not(:disabled) {
    border-color: #6ab0d0;
  }

  .tone-grow:hover:not(:disabled) {
    border-color: #6a9a48;
  }

  .tone-harvest:hover:not(:disabled) {
    border-color: #c8a040;
  }

  .tone-fire:hover:not(:disabled) {
    border-color: #d07830;
  }

  .tone-animal:hover:not(:disabled) {
    border-color: #9a7850;
  }

  .tone-market:hover:not(:disabled) {
    border-color: #c8a030;
  }

  .card-body {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
  }

  .card-label {
    font-size: 0.82rem;
    font-weight: 800;
    color: var(--panel-header);
    line-height: 1.2;
  }

  .card-hint {
    font-size: 0.65rem;
    font-weight: 500;
    color: var(--text-soft);
    line-height: 1.25;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .card-key {
    flex-shrink: 0;
    align-self: flex-start;
    min-width: 1.5rem;
    padding: 0.2rem 0.4rem;
    font-family: inherit;
    font-size: 0.68rem;
    font-weight: 800;
    line-height: 1;
    color: var(--panel-header);
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(110, 88, 62, 0.25);
    border-radius: 6px;
    box-shadow: 0 1px 0 rgba(110, 88, 62, 0.15);
  }

  .panel-foot {
    padding: 0.5rem 0.6rem;
    border-radius: 10px;
    background: rgba(0, 0, 0, 0.03);
    border: 1px dashed rgba(110, 88, 62, 0.25);
  }

  .foot-tip {
    margin: 0;
    font-size: 0.7rem;
    color: var(--text-soft);
    line-height: 1.45;
  }

  .foot-tip.secondary {
    margin-top: 0.35rem;
    font-size: 0.65rem;
    opacity: 0.9;
  }

  .foot-tip kbd {
    display: inline-flex;
    padding: 0.05rem 0.3rem;
    font-size: 0.62rem;
    font-weight: 700;
    background: #fff;
    border: 1px solid #c4b5a0;
    border-radius: 4px;
  }

  .link-btn {
    padding: 0;
    border: none;
    background: none;
    color: #5a7a28;
    font-size: inherit;
    font-weight: 700;
    text-decoration: underline;
    text-underline-offset: 2px;
    cursor: pointer;
  }

  .link-btn:hover {
    color: #3d5a18;
  }
</style>
