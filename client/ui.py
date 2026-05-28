"""
Farm Wars client UI helpers — warm palette, Russian copy, toasts, widgets.
"""

from __future__ import annotations

import time

import pygame

# --- Palette (warm farm) ---
BG_TOP = (72, 118, 168)
BG_BOTTOM = (143, 188, 120)
PANEL_BG = (248, 242, 228)
PANEL_BORDER = (120, 95, 70)
PANEL_HEADER = (90, 62, 40)
SOIL = (101, 73, 48)
SOIL_LIGHT = (139, 105, 72)
TILE_EMPTY = (160, 130, 90)
TILE_PLANT = (88, 145, 72)
TILE_SEL = (255, 210, 80)
TILE_SEL_GLOW = (255, 235, 160)
WATER_LOW = (180, 100, 80)
WATER_OK = (70, 150, 200)
GROWTH = (110, 185, 70)
GROWTH_READY = (255, 200, 50)
TEXT = (45, 38, 32)
TEXT_SOFT = (100, 88, 75)
TEXT_ON_DARK = (255, 252, 245)
ACCENT = (210, 120, 50)
ACCENT_HOVER = (230, 145, 70)
OK = (56, 140, 78)
ERROR = (200, 70, 60)
WARN = (200, 150, 50)
BTN_SECONDARY = (200, 185, 165)
BTN_SECONDARY_HOVER = (220, 205, 185)
MONEY = (255, 200, 60)

WIDTH, HEIGHT = 1280, 800
FARM_X, FARM_Y = 28, 108
TILE_SIZE = 80
TILE_GAP = 10
PANEL_X = 430
PANEL_W = WIDTH - PANEL_X - 20

PRODUCT_RU = {
    "wheat": "Пшеница",
    "corn": "Кукуруза",
    "potato": "Картофель",
    "flour": "Мука",
    "bread": "Хлеб",
    "cake": "Торт",
    "milk": "Молоко",
    "feed": "Корм",
}

RECIPE_RU = {
    "bread": "Мука ×2, пшеница ×1",
    "cake": "Мука ×3, молоко ×2",
}

EVENT_RU = {
    "PRODUCT_PURCHASED": "Куплено",
    "PURCHASE_FAILED": "Не купилось",
    "PLANT_PLACED": "Посажено",
    "PLANT_WATERED": "Полито",
    "PLANT_HARVESTED": "Собрано",
    "HARVEST_FAILED": "Не собрать",
    "PLANT_DIED": "Погибло",
    "RECIPE_STARTED": "В печи",
    "RECIPE_FINISHED": "Готово",
    "RECIPE_QUEUED": "В очереди",
    "RECIPE_REJECTED": "Рецепт нельзя",
    "MATCH_FINISHED": "Матч окончен",
    "CONTRACT_ERROR": "Ошибка",
}


PLANT_IDS = ("wheat", "corn", "potato")


def product_label(product_id: str) -> str:
    return PRODUCT_RU.get(product_id, product_id)


def crop_label(occupant_id: str | None) -> str:
    """
    Human name for a plant on a tile.

    Fixture uses instance ids (wheat_1); after world_factory prefix: p1_wheat_1.
    New plants use plant_id directly (wheat).
    """
    if not occupant_id:
        return "?"
    if occupant_id in PRODUCT_RU:
        return product_label(occupant_id)
    for plant_id in PLANT_IDS:
        if occupant_id == plant_id or f"_{plant_id}" in occupant_id or occupant_id.endswith(plant_id):
            return product_label(plant_id)
    return occupant_id


def load_fonts() -> dict[str, pygame.font.Font]:
    names = ["segoeui", "arial", "calibri", "tahoma"]
    title = body = small = None
    for name in names:
        try:
            title = pygame.font.SysFont(name, 32, bold=True)
            body = pygame.font.SysFont(name, 18)
            small = pygame.font.SysFont(name, 15)
            break
        except Exception:
            continue
    if body is None:
        body = pygame.font.SysFont(None, 20)
        small = pygame.font.SysFont(None, 16)
        title = pygame.font.SysFont(None, 28, bold=True)
    return {"title": title, "body": body, "small": small}


def draw_gradient_bg(screen: pygame.Surface) -> None:
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(BG_TOP[0] * (1 - t) + BG_BOTTOM[0] * t)
        g = int(BG_TOP[1] * (1 - t) + BG_BOTTOM[1] * t)
        b = int(BG_TOP[2] * (1 - t) + BG_BOTTOM[2] * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))


def draw_panel(screen: pygame.Surface, rect: pygame.Rect, title: str, fonts: dict) -> None:
    pygame.draw.rect(screen, PANEL_BG, rect, border_radius=12)
    pygame.draw.rect(screen, PANEL_BORDER, rect, 2, border_radius=12)
    header = pygame.Rect(rect.x, rect.y, rect.w, 36)
    pygame.draw.rect(screen, PANEL_HEADER, header, border_top_left_radius=12, border_top_right_radius=12)
    screen.blit(fonts["small"].render(title, True, TEXT_ON_DARK), (rect.x + 14, rect.y + 9))


def draw_text_field(screen: pygame.Surface, field, fonts: dict, label: str) -> None:
    screen.blit(fonts["small"].render(label, True, TEXT_SOFT), (field.rect.x, field.rect.y - 22))
    color = (255, 255, 250) if field.active else (240, 235, 225)
    pygame.draw.rect(screen, color, field.rect, border_radius=8)
    pygame.draw.rect(
        screen, ACCENT if field.active else PANEL_BORDER, field.rect, 2, border_radius=8
    )
    text = field.text if field.text else field.placeholder
    shade = TEXT_SOFT if not field.text else TEXT
    screen.blit(fonts["body"].render(text, True, shade), (field.rect.x + 10, field.rect.y + 8))


class Toast:
    __slots__ = ("text", "color", "until")

    def __init__(self, text: str, color: tuple, duration: float = 3.5):
        self.text = text
        self.color = color
        self.until = time.time() + duration


class ToastManager:
    def __init__(self):
        self._items: list[Toast] = []

    def push(self, text: str, kind: str = "info") -> None:
        colors = {"ok": OK, "error": ERROR, "warn": WARN, "info": PANEL_HEADER}
        self._items.append(Toast(text, colors.get(kind, PANEL_HEADER)))

    def from_events(self, events: list[dict]) -> None:
        for ev in events:
            msg = humanize_event(ev)
            if msg:
                kind = "error" if "ошиб" in msg.lower() or "не " in msg.lower() else "ok"
                if ev.get("event_type") in ("RECIPE_REJECTED", "PURCHASE_FAILED", "HARVEST_FAILED", "PLANT_DIED", "CONTRACT_ERROR"):
                    kind = "warn" if ev.get("event_type") != "CONTRACT_ERROR" else "error"
                self.push(msg, kind)

    def tick(self) -> None:
        now = time.time()
        self._items = [t for t in self._items if t.until > now]

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        self.tick()
        y = HEIGHT - 120
        for toast in self._items[-4:]:
            surf = font.render(toast.text, True, TEXT_ON_DARK)
            pad_x, pad_y = 14, 8
            box = surf.get_rect()
            box.w += pad_x * 2
            box.h += pad_y * 2
            box.centerx = WIDTH // 2
            box.y = y
            pygame.draw.rect(screen, toast.color, box, border_radius=10)
            screen.blit(surf, (box.x + pad_x, box.y + pad_y))
            y -= box.h + 8


def humanize_event(ev: dict) -> str | None:
    et = ev.get("event_type", "")
    pl = ev.get("payload") or {}
    base = EVENT_RU.get(et, et)

    if et == "PRODUCT_PURCHASED":
        return f"Куплено: {product_label(pl.get('product_id', '?'))}"
    if et == "PLANT_PLACED":
        return f"Посажено: {product_label(pl.get('plant_id', '?'))}"
    if et == "PLANT_WATERED":
        return "Растение полито"
    if et == "PLANT_HARVESTED":
        return f"Собрано: {product_label(pl.get('product_id', ''))} ×{pl.get('amount', 1)}"
    if et == "RECIPE_STARTED":
        return f"Печём: {product_label(pl.get('recipe_id', ''))}"
    if et == "RECIPE_FINISHED":
        return f"Готово: {product_label(pl.get('product_id', pl.get('recipe_id', '')))}"
    if et == "RECIPE_QUEUED":
        return f"В очереди: {product_label(pl.get('recipe_id', ''))}"
    if et == "PURCHASE_FAILED":
        reasons = {
            "NOT_ENOUGH_MONEY": "не хватает Bestiki",
            "UNKNOWN_PRODUCT": "нет такого товара",
        }
        return f"Покупка не удалась — {reasons.get(pl.get('reason'), pl.get('reason', ''))}"
    if et == "HARVEST_FAILED":
        reasons = {
            "NOT_READY": "сначала полей (вода < 50)",
            "NOT_RIPE": "ещё не созрело",
            "NO_PLANT": "здесь ничего не растёт",
            "EMPTY_TILE": "грядка пуста",
            "NOT_OWNER": "не твоя грядка",
            "UNKNOWN_TILE": "нет такой грядки",
        }
        return f"Сбор не вышел — {reasons.get(pl.get('reason'), pl.get('reason', ''))}"
    if et == "PLANT_DIED":
        return f"Растение погибло: {product_label(pl.get('plant_id', ''))}"
    if et == "RECIPE_REJECTED":
        reasons = {
            "NOT_ENOUGH_INGREDIENTS": "не хватает ингредиентов",
            "WRONG_BUILDING_TYPE": "не тот завод",
            "UNKNOWN_RECIPE": "нет такого рецепта",
        }
        return f"Рецепт не запущен — {reasons.get(pl.get('reason'), pl.get('reason', ''))}"
    if et == "MATCH_FINISHED":
        return f"Победитель: {pl.get('winner_player_id', '?')}"
    if et == "CONTRACT_ERROR":
        return pl.get("message") or base
    return None


class ActionButton:
    def __init__(self, rect, label: str, hotkey: str, action_id: str):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.hotkey = hotkey
        self.action_id = action_id
        self.enabled = True

    def draw(self, screen, fonts, mouse_pos):
        hover = self.enabled and self.rect.collidepoint(mouse_pos)
        if not self.enabled:
            bg = BTN_SECONDARY
        elif hover:
            bg = ACCENT_HOVER
        else:
            bg = ACCENT
        pygame.draw.rect(screen, bg, self.rect, border_radius=10)
        text_color = TEXT_ON_DARK if self.enabled else TEXT_SOFT
        screen.blit(
            fonts["body"].render(self.label, True, text_color),
            (self.rect.x + 12, self.rect.y + 6),
        )
        hk = fonts["small"].render(self.hotkey, True, (255, 255, 255) if self.enabled else TEXT_SOFT)
        screen.blit(hk, (self.rect.right - hk.get_width() - 10, self.rect.y + 8))

    def clicked(self, event) -> bool:
        return (
            self.enabled
            and event.type == pygame.MOUSEBUTTONDOWN
            and self.rect.collidepoint(event.pos)
        )


class ShopButton:
    def __init__(self, rect, product_id: str, price: int):
        self.rect = pygame.Rect(rect)
        self.product_id = product_id
        self.price = price

    def draw(self, screen, fonts, mouse_pos, can_afford: bool):
        hover = self.rect.collidepoint(mouse_pos)
        bg = BTN_SECONDARY_HOVER if hover else BTN_SECONDARY
        if not can_afford:
            bg = (200, 190, 185)
        pygame.draw.rect(screen, bg, self.rect, border_radius=8)
        label = f"{product_label(self.product_id)}  ·  {self.price} B"
        screen.blit(fonts["small"].render(label, True, TEXT if can_afford else TEXT_SOFT), (
            self.rect.x + 10, self.rect.y + 7,
        ))

    def clicked(self, event) -> bool:
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)


def draw_progress_bar(screen, rect, ratio: float, color, bg=(220, 210, 195)) -> None:
    pygame.draw.rect(screen, bg, rect, border_radius=4)
    inner = rect.copy()
    inner.w = max(0, int(rect.w * max(0, min(1, ratio))))
    if inner.w > 0:
        pygame.draw.rect(screen, color, inner, border_radius=4)


def draw_money_badge(screen, fonts, x, y, amount: int) -> None:
    text = f"{amount} Bestiki"
    surf = fonts["body"].render(text, True, TEXT)
    pad = 10
    box = surf.get_rect()
    box.topleft = (x, y)
    box.w += pad * 2
    box.h += pad
    pygame.draw.rect(screen, MONEY, box, border_radius=14)
    pygame.draw.rect(screen, PANEL_BORDER, box, 2, border_radius=14)
    screen.blit(surf, (box.x + pad, box.y + pad // 2))


def tile_hint(tile: dict | None, selected_seed: str) -> str:
    if tile is None:
        return "Выбери грядку — кликни по клетке слева"
    occ = tile.get("occupant_type", "EMPTY")
    water = tile.get("water_level")
    if occ == "EMPTY":
        return f"Пустая грядка · посадить: {product_label(selected_seed)} (T)"
    name = crop_label(tile.get("occupant_id"))
    growth_elapsed = tile.get("growth_elapsed_sec") or 0
    growth_needed = tile.get("growth_time_sec") or 0
    ripe = growth_needed > 0 and growth_elapsed >= growth_needed
    if ripe:
        return f"{name} · созрело — можно собирать (H)"
    if water is not None and water < 50:
        if growth_needed > 0:
            pct = min(100, int(growth_elapsed * 100 / growth_needed))
            return f"{name} · рост {pct}% · нужен полив (W)"
        return f"{name} · нужен полив (W)"
    if growth_needed > 0:
        pct = min(100, int(growth_elapsed * 100 / growth_needed))
        return f"{name} · рост {pct}%"
    if water is not None and water >= 50:
        return f"{name} · можно собирать (H)"
    return f"На грядке: {name}"
