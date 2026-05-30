# Farm Wars — web client

Svelte + TypeScript + Vite (SPA, **без SvelteKit**).

**Подробная документация:** [`../docs/frontend/README.md`](../docs/frontend/README.md) — архитектура, структура `src/`, синхронизация, UI, dev/LAN.

## Dev

```bash
# из корня репо
py -m server

cd web
npm install
npm run dev
```

http://localhost:5173 — запросы `/api/*` проксируются на `http://127.0.0.1:8765`.

## LAN

`web/.env.local`:

```
VITE_API_BASE=http://192.168.1.10:8765
```

## Build

```bash
npm run build
```

Артефакт: `dist/`

| Документ | Зачем |
|----------|--------|
| [`docs/frontend/README.md`](../docs/frontend/README.md) | индекс документации фронтенда |
| [`docs/frontend/development.md`](../docs/frontend/development.md) | env, build, чеклист фичи |
| [`docs/specs/client/002...`](../docs/specs/client/002.NIKITA.WEB_CLIENT_SVELTE_VITE.md) | ТЗ миграции и parity |
| [`AGENTS.md`](../AGENTS.md) | правила для ИИ при правках `web/` |
