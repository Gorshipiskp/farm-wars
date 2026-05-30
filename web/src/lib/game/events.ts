import type { GameEvent } from "$lib/api/types";
import { productLabel, animalLabel } from "./labels";

const WORLD_EVENT_RU: Record<string, string> = {
  DROUGHT: "Засуха",
  PESTS: "Вредители",
  STORM: "Шторм",
};

export function humanizeEvent(ev: GameEvent): string | null {
  const et = ev.event_type ?? "";
  const pl = ev.payload ?? {};

  if (et === "PRODUCT_PURCHASED") {
    return `Куплено: ${productLabel(String(pl.product_id ?? "?"))}`;
  }
  if (et === "PRODUCT_SOLD") {
    return `Продано: ${productLabel(String(pl.product_id ?? "?"))} +${pl.total_earned ?? 0} B`;
  }
  if (et === "STIPEND_GRANTED") {
    return `Поддержка фермы: +${pl.amount ?? 0} B`;
  }
  if (et === "SELL_FAILED") {
    const reasons: Record<string, string> = {
      NOT_ENOUGH_PRODUCT: "нет в сумке",
      NOT_SELLABLE: "нельзя продать",
      UNKNOWN_PRODUCT: "нет товара",
    };
    const r = String(pl.reason ?? "");
    return `Продажа не вышла — ${reasons[r] ?? r}`;
  }
  if (et === "PLANT_PLACED") {
    return `Посажено: ${productLabel(String(pl.plant_id ?? "?"))}`;
  }
  if (et === "PLANT_WATERED") return "Растение полито";
  if (et === "PLANT_HARVESTED") {
    return `Собрано: ${productLabel(String(pl.product_id ?? ""))} ×${pl.amount ?? 1}`;
  }
  if (et === "RECIPE_STARTED") {
    return `Печём: ${productLabel(String(pl.recipe_id ?? ""))}`;
  }
  if (et === "RECIPE_FINISHED") {
    return `Готово: ${productLabel(String(pl.product_id ?? pl.recipe_id ?? ""))}`;
  }
  if (et === "PURCHASE_FAILED") {
    const reasons: Record<string, string> = {
      NOT_ENOUGH_MONEY: "не хватает Bestiki",
      UNKNOWN_PRODUCT: "нет такого товара",
    };
    const r = String(pl.reason ?? "");
    return `Покупка не удалась — ${reasons[r] ?? r}`;
  }
  if (et === "HARVEST_FAILED") {
    const reasons: Record<string, string> = {
      NOT_READY: "сначала полей (вода < 50)",
      NOT_RIPE: "ещё не созрело",
      NO_PLANT: "здесь ничего не растёт",
      EMPTY_TILE: "грядка пуста",
      NOT_OWNER: "не твоя грядка",
      UNKNOWN_TILE: "нет такой грядки",
    };
    const r = String(pl.reason ?? "");
    return `Сбор не вышел — ${reasons[r] ?? r}`;
  }
  if (et === "PLANT_DIED") {
    return `Растение погибло: ${productLabel(String(pl.plant_id ?? ""))}`;
  }
  if (et === "RECIPE_REJECTED") {
    const reasons: Record<string, string> = {
      NOT_ENOUGH_INGREDIENTS: "не хватает ингредиентов",
      WRONG_BUILDING_TYPE: "не тот завод",
      UNKNOWN_RECIPE: "нет такого рецепта",
    };
    const r = String(pl.reason ?? "");
    return `Рецепт не запущен — ${reasons[r] ?? r}`;
  }
  if (et === "MATCH_FINISHED") {
    return `Победитель: ${pl.winner_player_id ?? "?"}`;
  }
  if (et === "ANIMAL_PURCHASED") return "Куплена корова";
  if (et === "ANIMAL_FED") {
    return `Покормлено: ${animalLabel(String(pl.animal_id ?? "cow"))}`;
  }
  if (et === "ANIMAL_PRODUCED") {
    const pid = String(pl.product_id ?? "milk");
    const verb =
      pid === "milk"
        ? "Надоено"
        : pid === "egg"
          ? "Снесено"
          : pid === "wool"
            ? "Пострижено"
            : "Получено";
    return `${verb}: ${productLabel(pid)}`;
  }
  if (et === "FEED_FAILED") {
    const reasons: Record<string, string> = {
      NOT_ENOUGH_MONEY: "не хватает Bestiki",
      NO_ANIMAL: "нет животного",
      WRONG_ZONE: "не загон",
      NOT_OWNER: "не твой загон",
    };
    const r = String(pl.reason ?? "");
    return `Кормление не вышло — ${reasons[r] ?? r}`;
  }
  if (et === "WATER_FAILED") {
    const reasons: Record<string, string> = {
      NOT_ENOUGH_MONEY: "не хватает Bestiki",
    };
    const r = String(pl.reason ?? "");
    return `Полив не вышел — ${reasons[r] ?? r}`;
  }
  if (et === "ANIMAL_PURCHASE_FAILED") {
    const reasons: Record<string, string> = {
      NOT_ENOUGH_MONEY: "не хватает Bestiki",
      TILE_OCCUPIED: "загон занят",
      WRONG_ZONE: "нужен загон",
    };
    const r = String(pl.reason ?? "");
    return `Корова не куплена — ${reasons[r] ?? r}`;
  }
  if (et === "SABOTAGE_APPLIED") {
    return `Саботаж: ${pl.sabotage_id ?? "?"} → ${pl.effect ?? ""}`;
  }
  if (et === "SABOTAGE_FAILED") {
    const reasons: Record<string, string> = {
      NOT_ENOUGH_MONEY: "не хватает Bestiki",
      OWN_TILE: "нельзя по своей клетке",
      UNKNOWN_TILE: "нет клетки",
    };
    const r = String(pl.reason ?? "");
    return `Саботаж не вышел — ${reasons[r] ?? r}`;
  }
  if (et === "EVENT_TRIGGERED") {
    const wt = String(pl.event_type ?? "");
    const name = String(pl.display_name ?? WORLD_EVENT_RU[wt] ?? wt);
    const affected = pl.affected_tiles;
    if (affected != null) {
      return `Событие: ${name} (затронуто: ${affected})`;
    }
    return `Событие: ${name}`;
  }
  if (et === "CONTRACT_ERROR") {
    return String(pl.message ?? "Ошибка контракта");
  }
  return null;
}

function shouldSkipEvent(ev: GameEvent, myPlayerId: string): boolean {
  const pl = ev.payload ?? {};
  if (
    ev.event_type === "SABOTAGE_APPLIED" &&
    pl.is_hidden &&
    pl.player_id !== myPlayerId
  ) {
    return true;
  }
  if (ev.event_type === "STIPEND_GRANTED" && pl.player_id !== myPlayerId) {
    return true;
  }
  const evPlayer = pl.player_id;
  if (evPlayer && evPlayer !== myPlayerId) {
    const skipTypes = new Set([
      "CONTRACT_ERROR",
      "HARVEST_FAILED",
      "FEED_FAILED",
      "WATER_FAILED",
      "RECIPE_REJECTED",
      "PURCHASE_FAILED",
      "SELL_FAILED",
      "ANIMAL_PURCHASE_FAILED",
      "SABOTAGE_FAILED",
    ]);
    if (skipTypes.has(ev.event_type ?? "")) return true;
  }
  return false;
}

function toastKind(eventType: string): "ok" | "error" | "warn" | "info" {
  if (eventType === "STIPEND_GRANTED") return "info";
  if (eventType === "CONTRACT_ERROR") return "error";
  if (
    [
      "RECIPE_REJECTED",
      "PURCHASE_FAILED",
      "HARVEST_FAILED",
      "FEED_FAILED",
      "WATER_FAILED",
      "ANIMAL_PURCHASE_FAILED",
    ].includes(eventType)
  ) {
    return "warn";
  }
  return "ok";
}

let prevEvents: GameEvent[] = [];

export function resetEventFeed(): void {
  prevEvents = [];
}

export function feedToasts(
  events: GameEvent[],
  myPlayerId: string,
  push: (msg: string, kind: "ok" | "error" | "warn" | "info") => void,
): void {
  if (events === prevEvents) return;
  if (events.length > prevEvents.length) {
    for (const ev of events.slice(prevEvents.length)) {
      if (shouldSkipEvent(ev, myPlayerId)) continue;
      const msg = humanizeEvent(ev);
      if (msg) push(msg, toastKind(ev.event_type ?? ""));
    }
  }
  prevEvents = [...events];
}
