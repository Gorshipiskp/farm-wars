"""
Farm Wars client UI helpers — warm palette, Russian copy, toasts, widgets.
"""

from __future__ import annotations

import time

import pygame

# --- Palette (warm farm) ---
BG_TOP = (58, 98, 148)
BG_BOTTOM = (118, 168, 108)
SKY_GLOW = (120, 160, 200, 40)
PANEL_BG = (252, 248, 238)
PANEL_BG_DARK = (242, 232, 214)
PANEL_BORDER = (110, 88, 62)
PANEL_HEADER = (78, 52, 36)
PANEL_SHADOW = (40, 30, 20, 55)
SOIL = (92, 66, 42)
SOIL_LIGHT = (148, 118, 82)
TILE_EMPTY = (175, 145, 102)
TILE_PLANT = (72, 138, 78)
TILE_ANIMAL = (108, 88, 150)
TILE_ANIMAL_EMPTY = (145, 128, 118)
TILE_ENEMY = (190, 88, 88)
TILE_ENEMY_EMPTY = (150, 118, 118)
MILK = (210, 225, 255)
TILE_SEL = (255, 210, 70)
TILE_SEL_GLOW = (255, 240, 170)
WATER_LOW = (210, 110, 85)
WATER_CRITICAL = (196, 56, 40)
WATER_OK = (65, 155, 210)
HUNGER_LOW = (220, 150, 60)
HUNGER_CRITICAL = (184, 48, 48)
WATER_LOW_THRESHOLD = 50
WATER_CRITICAL_THRESHOLD = 25
ANIMAL_HUNGER_WARN_TICKS = 30
ANIMAL_HUNGER_STOP_TICKS = 40
GROWTH = (95, 175, 75)
GROWTH_READY = (255, 195, 45)
TEXT = (42, 36, 30)
TEXT_SOFT = (105, 92, 78)
TEXT_ON_DARK = (255, 252, 245)
ACCENT = (205, 115, 48)
ACCENT_HOVER = (228, 140, 65)
OK = (52, 135, 72)
ERROR = (195, 65, 55)
WARN = (210, 145, 42)
BTN_SECONDARY = (215, 200, 178)
BTN_SECONDARY_HOVER = (232, 218, 198)
MONEY = (255, 210, 55)
MONEY_BORDER = (180, 140, 30)
HINT_BG = (255, 253, 245)
HINT_BORDER = (200, 185, 160)
HEADER_BAR = (55, 45, 38, 140)

WIDTH, HEIGHT = 1280, 800
FARM_X, FARM_Y = 24, 108
FARM_COLS = 4
FARM_PLANT_SLOTS = 12
FARM_ANIMAL_SLOTS = 8
FARM_TILE_COUNT = FARM_PLANT_SLOTS + FARM_ANIMAL_SLOTS
TILE_SIZE = 62
TILE_GAP = 8


def farm_grid_width(cols: int = FARM_COLS) -> int:
    return cols * (TILE_SIZE + TILE_GAP) - TILE_GAP


def farm_panel_inner_width() -> int:
    return farm_grid_width() + 8


def farm_grid_height(tile_count: int | None = None) -> int:
    n = FARM_TILE_COUNT if tile_count is None else tile_count
    rows = max(1, (max(1, n) - 1) // FARM_COLS + 1)
    return rows * (TILE_SIZE + TILE_GAP) - TILE_GAP


PANEL_X = FARM_X + farm_panel_inner_width() + 36
PANEL_W = WIDTH - PANEL_X - 16

SIDEBAR_ACTION_BTN_W = 118
SIDEBAR_ACTION_BTN_H = 28
SIDEBAR_ACTION_GAP = 5
SIDEBAR_SCROLL_STEP = 28

HINT_Y = FARM_Y + farm_grid_height() + 12
# Single opponent: compact row; 2+ opponents: tab picker row above label.
OPPONENT_PICKER_Y = HINT_Y + 4
OPPONENT_LABEL_Y_SINGLE = HINT_Y + 30
OPPONENT_LABEL_Y_MULTI = HINT_Y + 52
OPPONENT_FARM_Y_SINGLE = OPPONENT_LABEL_Y_SINGLE + 22
OPPONENT_FARM_Y_MULTI = OPPONENT_LABEL_Y_MULTI + 22
OPPONENT_LABEL_Y = OPPONENT_LABEL_Y_SINGLE
OPPONENT_FARM_Y = OPPONENT_FARM_Y_MULTI
OPPONENT_FARM_Y_OFFSET = OPPONENT_FARM_Y - FARM_Y
BAKERY_Y = OPPONENT_FARM_Y + farm_grid_height() + 8
HOTKEY_BAR_Y = BAKERY_Y + 32
FARM_PANEL_H = HOTKEY_BAR_Y + 24 - (FARM_Y - 36)

PRODUCT_COLORS = {
    "wheat": (230, 200, 90),
    "corn": (240, 210, 70),
    "potato": (210, 170, 120),
    "tomato": (220, 70, 60),
    "carrot": (230, 140, 50),
    "sunflower": (255, 220, 50),
    "flour": (245, 240, 220),
    "bread": (210, 150, 80),
    "cake": (255, 180, 200),
    "cheese": (255, 235, 120),
    "butter": (255, 245, 180),
    "sausage": (180, 90, 70),
    "pie": (200, 120, 80),
    "soup": (200, 100, 60),
    "omelette": (255, 230, 150),
    "milk": (240, 248, 255),
    "egg": (255, 250, 230),
    "wool": (200, 200, 210),
    "pork": (220, 160, 150),
    "feed": (160, 130, 90),
    "wheat_seed": (200, 180, 100),
    "corn_seed": (210, 190, 90),
    "potato_seed": (190, 160, 110),
    "tomato_seed": (200, 90, 80),
    "carrot_seed": (220, 150, 70),
    "sunflower_seed": (240, 210, 60),
}

_bg_cache: pygame.Surface | None = None


def is_left_click(event) -> bool:
    return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1


PRODUCT_RU = {
    "wheat": "Пшеница",
    "corn": "Кукуруза",
    "potato": "Картофель",
    "tomato": "Помидор",
    "carrot": "Морковь",
    "sunflower": "Подсолнечник",
    "wheat_seed": "Семена пшеницы",
    "corn_seed": "Семена кукурузы",
    "potato_seed": "Семена картофеля",
    "tomato_seed": "Семена томата",
    "carrot_seed": "Семена моркови",
    "sunflower_seed": "Семена подсолнечника",
    "flour": "Мука",
    "bread": "Хлеб",
    "cake": "Торт",
    "cheese": "Сыр",
    "butter": "Масло",
    "sausage": "Колбаса",
    "pie": "Пирог",
    "soup": "Суп",
    "omelette": "Омлет",
    "milk": "Молоко",
    "egg": "Яйцо",
    "wool": "Шерсть",
    "pork": "Свинина",
    "feed": "Корм",
}

RECIPE_RU = {
    "bread": "Мука ×2, пшеница ×1",
    "cake": "Мука ×3, молоко ×2",
    "pie": "Мука ×2, яйцо ×2, пшеница ×1",
    "soup": "Помидор ×2, картофель ×1, морковь ×1",
    "omelette": "Яйцо ×3, молоко ×1",
    "cheese": "Молоко ×2",
    "butter": "Молоко ×1, мука ×1",
    "sausage": "Свинина ×2, мука ×1",
}

EVENT_RU = {
    "PRODUCT_PURCHASED": "Куплено",
    "PRODUCT_SOLD": "Продано",
    "PURCHASE_FAILED": "Не купилось",
    "SELL_FAILED": "Не продалось",
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
    "EVENT_TRIGGERED": "Событие",
    "ANIMAL_PURCHASED": "Куплена корова",
    "ANIMAL_PURCHASE_FAILED": "Не купить",
    "ANIMAL_FED": "Покормлено",
    "ANIMAL_PRODUCED": "Надоено",
    "FEED_FAILED": "Не покормить",
    "WATER_FAILED": "Не полить",
    "SABOTAGE_APPLIED": "Саботаж",
    "SABOTAGE_FAILED": "Саботаж не вышел",
    "CONTRACT_ERROR": "Ошибка",
}

ANIMAL_RU = {
    "cow": "Корова",
    "chicken": "Курица",
    "sheep": "Овца",
    "pig": "Свинья",
}

WORLD_EVENT_RU = {
    "DROUGHT": "Засуха",
    "RAIN": "Дождь",
    "FLOOD": "Наводнение",
    "EARTHQUAKE": "Землетрясение",
    "EPIDEMIC": "Эпидемия",
}

PLANT_IDS = ("wheat", "corn", "potato", "tomato", "carrot", "sunflower")

HOTKEY_HELP = (
    ("W", "полив"),
    ("T", "посадка"),
    ("H", "сбор"),
    ("B", "печь"),
    ("V", "продажа"),
    ("X", "саботаж"),
    ("Esc", "меню"),
)


def product_label(product_id: str) -> str:
    return PRODUCT_RU.get(product_id, product_id)


def is_seed_product(product_id: str) -> bool:
    return product_id.endswith("_seed")


def is_bag_product(product_id: str) -> bool:
    """Inventory shown as harvest/goods (not planting seeds)."""
    return not is_seed_product(product_id)


def plant_crop_label(plant_id: str, plants_meta: dict | None = None) -> str:
    if plants_meta and plant_id in plants_meta:
        return plants_meta[plant_id].get("crop_display_name") or product_label(plant_id)
    return product_label(plant_id)


def seed_label_for_plant(plant_id: str, plants_meta: dict | None = None) -> str:
    if plants_meta and plant_id in plants_meta:
        return plants_meta[plant_id].get("seed_display_name") or product_label(
            plants_meta[plant_id].get("seed_product_id", plant_id)
        )
    return product_label(f"{plant_id}_seed") if not plant_id.endswith("_seed") else product_label(plant_id)


def animal_label(animal_id: str | None) -> str:
    if not animal_id:
        return "?"
    return ANIMAL_RU.get(animal_id, animal_id)


def crop_label(occupant_id: str | None) -> str:
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
            title = pygame.font.SysFont(name, 34, bold=True)
            body = pygame.font.SysFont(name, 18)
            small = pygame.font.SysFont(name, 15)
            tiny = pygame.font.SysFont(name, 13)
            break
        except Exception:
            continue
    if body is None:
        body = pygame.font.SysFont(None, 20)
        small = pygame.font.SysFont(None, 16)
        title = pygame.font.SysFont(None, 30, bold=True)
        tiny = pygame.font.SysFont(None, 14)
    return {"title": title, "body": body, "small": small, "tiny": tiny}


def _build_gradient() -> pygame.Surface:
    surf = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(BG_TOP[0] * (1 - t) + BG_BOTTOM[0] * t)
        g = int(BG_TOP[1] * (1 - t) + BG_BOTTOM[1] * t)
        b = int(BG_TOP[2] * (1 - t) + BG_BOTTOM[2] * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (WIDTH, y))
    # Soft sun glow top-right
    glow = pygame.Surface((420, 280), pygame.SRCALPHA)
    for i in range(8, 0, -1):
        alpha = 18 + i * 4
        pygame.draw.ellipse(
            glow,
            (255, 248, 200, alpha),
            (20 - i * 8, 10 - i * 6, 360 + i * 16, 220 + i * 12),
        )
    surf.blit(glow, (WIDTH - 400, 20))
    return surf


def draw_gradient_bg(screen: pygame.Surface) -> None:
    global _bg_cache
    if _bg_cache is None:
        _bg_cache = _build_gradient()
    screen.blit(_bg_cache, (0, 0))


def _shadow_rect(screen, rect: pygame.Rect, radius: int = 12, offset: int = 3) -> None:
    sh = rect.copy()
    sh.x += offset
    sh.y += offset
    pygame.draw.rect(screen, (30, 25, 20), sh, border_radius=radius)


def draw_panel(screen: pygame.Surface, rect: pygame.Rect, title: str, fonts: dict) -> None:
    _shadow_rect(screen, rect)
    pygame.draw.rect(screen, PANEL_BG, rect, border_radius=14)
    pygame.draw.rect(screen, PANEL_BORDER, rect, 2, border_radius=14)
    header = pygame.Rect(rect.x, rect.y, rect.w, 40)
    pygame.draw.rect(
        screen,
        PANEL_HEADER,
        header,
        border_top_left_radius=14,
        border_top_right_radius=14,
    )
    screen.blit(fonts["small"].render(title, True, TEXT_ON_DARK), (rect.x + 16, rect.y + 11))


def draw_section_label(screen, fonts, x: int, y: int, text: str, *, line_w: int = 200) -> int:
    screen.blit(fonts["body"].render(text, True, TEXT), (x, y))
    line_y = y + 24
    pygame.draw.line(screen, PANEL_BORDER, (x, line_y), (x + line_w, line_y), 1)
    return line_y + 10


def draw_section_header(
    screen,
    fonts,
    x: int,
    y: int,
    title: str,
    hint: str | None = None,
    *,
    line_w: int = 280,
) -> int:
    screen.blit(fonts["body"].render(title, True, TEXT), (x, y))
    if hint:
        hint_surf = fonts["tiny"].render(hint, True, TEXT_SOFT)
        screen.blit(hint_surf, (x + fonts["body"].size(title)[0] + 8, y + 4))
    line_y = y + 22
    pygame.draw.line(screen, PANEL_BORDER, (x, line_y), (x + line_w, line_y), 1)
    return line_y + 8


def draw_text_field(screen: pygame.Surface, field, fonts: dict, label: str) -> None:
    screen.blit(fonts["small"].render(label, True, TEXT_SOFT), (field.rect.x, field.rect.y - 22))
    color = (255, 255, 252) if field.active else (248, 244, 236)
    _shadow_rect(screen, field.rect, radius=8, offset=2)
    pygame.draw.rect(screen, color, field.rect, border_radius=8)
    pygame.draw.rect(
        screen, ACCENT if field.active else PANEL_BORDER, field.rect, 2, border_radius=8
    )
    text = field.text if field.text else field.placeholder
    shade = TEXT_SOFT if not field.text else TEXT
    screen.blit(fonts["body"].render(text, True, shade), (field.rect.x + 12, field.rect.y + 9))


def draw_status_pill(screen, fonts, y: int, text: str, *, ok: bool = True) -> None:
    color = OK if ok else ERROR
    surf = fonts["small"].render(text, True, TEXT_ON_DARK)
    pad_x, pad_y = 16, 8
    box = surf.get_rect()
    box.w += pad_x * 2
    box.h += pad_y * 2
    box.x = 40
    box.y = y
    pygame.draw.rect(screen, (30, 30, 30, 120), box.move(0, 2), border_radius=20)
    pygame.draw.rect(screen, color, box, border_radius=20)
    screen.blit(surf, (box.x + pad_x, box.y + pad_y))


def draw_match_header(
    screen,
    fonts,
    *,
    player_name: str,
    money: int,
    tick: int,
    join_code: str = "",
    is_host: bool = False,
) -> None:
    bar = pygame.Rect(0, 0, WIDTH, 56)
    bar_surf = pygame.Surface((WIDTH, 56), pygame.SRCALPHA)
    bar_surf.fill(HEADER_BAR)
    screen.blit(bar_surf, (0, 0))
    screen.blit(
        fonts["title"].render("Farm Wars", True, TEXT_ON_DARK),
        (FARM_X, 12),
    )
    name_surf = fonts["body"].render(player_name, True, ACCENT_HOVER)
    screen.blit(name_surf, (FARM_X + 160, 16))
    draw_money_badge(screen, fonts, PANEL_X - 10, 10, money)
    tick_text = f"тик {tick}"
    tick_surf = fonts["small"].render(tick_text, True, TEXT_ON_DARK)
    screen.blit(tick_surf, (PANEL_X - 10 - tick_surf.get_width() - 12, 18))
    if join_code:
        role = "хост" if is_host else "гость"
        code_surf = fonts["tiny"].render(f"{role} · код {join_code}", True, (220, 220, 220))
        screen.blit(code_surf, (FARM_X + 160, 36))


def draw_farm_card(screen, rect: pygame.Rect) -> None:
    _shadow_rect(screen, rect, radius=16)
    pygame.draw.rect(screen, SOIL_LIGHT, rect, border_radius=16)
    inner = rect.inflate(-6, -6)
    pygame.draw.rect(screen, (125, 95, 62), inner, border_radius=14)
    pygame.draw.rect(screen, SOIL, inner, 2, border_radius=14)


def draw_zone_label(screen, fonts, x: int, y: int, text: str, *, enemy: bool = False) -> None:
    color = TILE_ENEMY if enemy else TEXT_ON_DARK
    pad = 8
    surf = fonts["small"].render(text, True, color)
    box = surf.get_rect()
    box.topleft = (x, y)
    box.w += pad * 2
    box.h += 4
    bg = (80, 40, 40, 160) if enemy else (50, 40, 30, 140)
    badge = pygame.Surface((box.w, box.h), pygame.SRCALPHA)
    badge.fill(bg)
    screen.blit(badge, box.topleft)
    screen.blit(surf, (x + pad, y + 2))


def draw_hint_bar(screen, fonts, rect: pygame.Rect, text: str) -> None:
    accent = ACCENT
    low = "полив" in text.lower() or "вода" in text.lower()
    ripe = "созрело" in text.lower() or "собери" in text.lower()
    enemy = "соперник" in text.lower()
    if enemy:
        accent = TILE_ENEMY
    elif ripe:
        accent = GROWTH_READY
    elif low:
        accent = WATER_LOW
    _shadow_rect(screen, rect, radius=8, offset=2)
    pygame.draw.rect(screen, HINT_BG, rect, border_radius=8)
    pygame.draw.rect(screen, HINT_BORDER, rect, 1, border_radius=8)
    stripe = pygame.Rect(rect.x, rect.y + 4, 4, rect.h - 8)
    pygame.draw.rect(screen, accent, stripe, border_radius=2)
    screen.blit(fonts["small"].render(text, True, TEXT), (rect.x + 14, rect.y + 7))


def draw_hotkey_bar(screen, fonts, x: int, y: int, max_w: int) -> None:
    cx = x
    for key, label in HOTKEY_HELP:
        key_s = fonts["tiny"].render(key, True, TEXT_ON_DARK)
        lab_s = fonts["tiny"].render(label, True, (230, 225, 215))
        kw, kh = key_s.get_size()
        box = pygame.Rect(cx, y, kw + 10, kh + 6)
        pygame.draw.rect(screen, (60, 50, 40, 180), box, border_radius=4)
        screen.blit(key_s, (box.x + 5, box.y + 3))
        cx = box.right + 4
        screen.blit(lab_s, (cx, y + 4))
        cx += lab_s.get_width() + 14
        if cx > x + max_w:
            break


def draw_product_icon(screen, center: tuple[int, int], product_id: str, radius: int = 10) -> None:
    color = PRODUCT_COLORS.get(product_id, (180, 180, 180))
    pygame.draw.circle(screen, (40, 30, 20), center, radius + 1)
    pygame.draw.circle(screen, color, center, radius)
    letter = product_id[:1].upper() if product_id else "?"
    font = pygame.font.SysFont("arial", max(10, radius))
    surf = font.render(letter, True, (50, 40, 30))
    screen.blit(surf, surf.get_rect(center=center))


def draw_bakery_chip(screen, fonts, x: int, y: int, text: str, *, active: bool) -> None:
    surf = fonts["small"].render(text, True, TEXT_ON_DARK if active else TEXT_SOFT)
    pad = (10, 5)
    box = surf.get_rect()
    box.topleft = (x, y)
    box.w += pad[0] * 2
    box.h += pad[1] * 2
    bg = ACCENT if active else (100, 90, 80)
    pygame.draw.rect(screen, bg, box, border_radius=12)
    screen.blit(surf, (box.x + pad[0], box.y + pad[1]))


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
                if ev.get("event_type") in (
                    "RECIPE_REJECTED",
                    "PURCHASE_FAILED",
                    "HARVEST_FAILED",
                    "PLANT_DIED",
                    "EVENT_TRIGGERED",
                    "CONTRACT_ERROR",
                ):
                    kind = "warn" if ev.get("event_type") != "CONTRACT_ERROR" else "error"
                self.push(msg, kind)

    def tick(self) -> None:
        now = time.time()
        self._items = [t for t in self._items if t.until > now]

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        self.tick()
        y = HEIGHT - 100
        for toast in self._items[-4:]:
            surf = font.render(toast.text, True, TEXT_ON_DARK)
            pad_x, pad_y = 16, 10
            box = surf.get_rect()
            box.w += pad_x * 2
            box.h += pad_y * 2
            box.centerx = WIDTH // 2
            box.y = y
            pygame.draw.rect(screen, (25, 20, 15), box.move(0, 3), border_radius=12)
            pygame.draw.rect(screen, toast.color, box, border_radius=12)
            screen.blit(surf, (box.x + pad_x, box.y + pad_y))
            y -= box.h + 10


def humanize_event(ev: dict) -> str | None:
    et = ev.get("event_type", "")
    pl = ev.get("payload") or {}
    base = EVENT_RU.get(et, et)

    if et == "PRODUCT_PURCHASED":
        return f"Куплено: {product_label(pl.get('product_id', '?'))}"
    if et == "PRODUCT_SOLD":
        return f"Продано: {product_label(pl.get('product_id', '?'))} +{pl.get('total_earned', 0)} B"
    if et == "SELL_FAILED":
        reasons = {
            "NOT_ENOUGH_PRODUCT": "нет в сумке",
            "NOT_SELLABLE": "нельзя продать",
            "UNKNOWN_PRODUCT": "нет товара",
        }
        return f"Продажа не вышла — {reasons.get(pl.get('reason'), pl.get('reason', ''))}"
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
    if et == "ANIMAL_PURCHASED":
        return "Куплена корова"
    if et == "ANIMAL_FED":
        return f"Покормлено: {animal_label(pl.get('animal_id', 'cow'))}"
    if et == "ANIMAL_PRODUCED":
        return f"Надоено: {product_label(pl.get('product_id', 'milk'))}"
    if et == "FEED_FAILED":
        reasons = {
            "NOT_ENOUGH_MONEY": "не хватает Bestiki",
            "NO_ANIMAL": "нет животного",
            "WRONG_ZONE": "не загон",
            "NOT_OWNER": "не твой загон",
        }
        return f"Кормление не вышло — {reasons.get(pl.get('reason'), pl.get('reason', ''))}"
    if et == "WATER_FAILED":
        reasons = {
            "NOT_ENOUGH_MONEY": "не хватает Bestiki",
        }
        return f"Полив не вышел — {reasons.get(pl.get('reason'), pl.get('reason', ''))}"
    if et == "ANIMAL_PURCHASE_FAILED":
        reasons = {
            "NOT_ENOUGH_MONEY": "не хватает Bestiki",
            "TILE_OCCUPIED": "загон занят",
            "WRONG_ZONE": "нужен загон",
        }
        return f"Корова не куплена — {reasons.get(pl.get('reason'), pl.get('reason', ''))}"
    if et == "SABOTAGE_APPLIED":
        return f"Саботаж: {pl.get('sabotage_id', '?')} → {pl.get('effect', '')}"
    if et == "SABOTAGE_FAILED":
        reasons = {
            "NOT_ENOUGH_MONEY": "не хватает Bestiki",
            "OWN_TILE": "нельзя по своей клетке",
            "UNKNOWN_TILE": "нет клетки",
        }
        return f"Саботаж не вышел — {reasons.get(pl.get('reason'), pl.get('reason', ''))}"
    if et == "EVENT_TRIGGERED":
        wt = pl.get("event_type", "")
        name = pl.get("display_name") or WORLD_EVENT_RU.get(wt, wt)
        affected = pl.get("affected_tiles")
        if affected is not None:
            return f"Событие: {name} (затронуто: {affected})"
        return f"Событие: {name}"
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

    def draw(self, screen, fonts, mouse_pos, *, compact: bool = False):
        hover = self.enabled and self.rect.collidepoint(mouse_pos)
        if not self.enabled:
            bg = BTN_SECONDARY
            text_color = TEXT_SOFT
            border = PANEL_BORDER
        elif hover:
            bg = ACCENT
            text_color = TEXT_ON_DARK
            border = (160, 90, 35)
        else:
            bg = BTN_SECONDARY
            text_color = TEXT
            border = PANEL_BORDER
        if self.enabled and hover:
            _shadow_rect(screen, self.rect, radius=8, offset=2)
        radius = 8 if compact else 10
        pygame.draw.rect(screen, bg, self.rect, border_radius=radius)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=radius)
        label_font = fonts["small"] if compact else fonts["body"]
        screen.blit(
            label_font.render(self.label, True, text_color),
            (self.rect.x + (8 if compact else 12), self.rect.y + (5 if compact else 7)),
        )
        hk_size = 18 if compact else 22
        hk_bg = pygame.Rect(
            self.rect.right - hk_size - 4,
            self.rect.centery - hk_size // 2,
            hk_size,
            hk_size,
        )
        pygame.draw.rect(screen, (255, 255, 255, 60) if self.enabled else (0, 0, 0, 30), hk_bg, border_radius=4)
        hk = fonts["tiny" if compact else "small"].render(self.hotkey, True, text_color)
        screen.blit(hk, hk.get_rect(center=hk_bg.center))

    def clicked(self, event) -> bool:
        return self.enabled and is_left_click(event) and self.rect.collidepoint(event.pos)


class ShopButton:
    def __init__(self, rect, product_id: str, price: int):
        self.rect = pygame.Rect(rect)
        self.product_id = product_id
        self.price = price

    def draw(self, screen, fonts, mouse_pos, can_afford: bool):
        hover = self.rect.collidepoint(mouse_pos) and can_afford
        bg = BTN_SECONDARY_HOVER if hover else BTN_SECONDARY
        if not can_afford:
            bg = (210, 205, 198)
        if hover:
            _shadow_rect(screen, self.rect, radius=8, offset=2)
        pygame.draw.rect(screen, bg, self.rect, border_radius=8)
        if can_afford:
            draw_product_icon(screen, (self.rect.x + 18, self.rect.centery), self.product_id, 9)
        label = product_label(self.product_id)
        if len(label) > 16:
            label = label[:15] + "…"
        line = f"{label}  ·  {self.price} B"
        screen.blit(
            fonts["tiny"].render(line, True, TEXT if can_afford else TEXT_SOFT),
            (self.rect.x + 28, self.rect.y + 8),
        )

    def clicked(self, event) -> bool:
        return is_left_click(event) and self.rect.collidepoint(event.pos)


class SeedPicker:
    """Plant selection — shows crop name + seed count in inventory."""

    def __init__(self):
        self._rects: list[tuple[str, pygame.Rect]] = []

    def clear(self) -> None:
        self._rects = []

    def hit(self, pos) -> str | None:
        for seed_id, rect in self._rects:
            if rect.collidepoint(pos):
                return seed_id
        return None

    def draw(
        self,
        screen,
        fonts,
        x: int,
        y: int,
        seeds: tuple[str, ...],
        selected: str,
        player: dict | None,
        plants_meta: dict | None = None,
        *,
        max_w: int = 320,
        hotkey_index: bool = True,
    ) -> int:
        self._rects = []
        gap = 6
        cols = max(1, min(3, (max_w + gap) // (108 + gap)))
        chip_w = (max_w - (cols - 1) * gap) // cols if cols else max_w
        chip_h = 40
        for i, plant_id in enumerate(seeds):
            col = i % cols
            row = i // cols
            cx = x + col * (chip_w + gap)
            cy = y + row * (chip_h + gap)
            meta = (plants_meta or {}).get(plant_id, {})
            seed_pid = meta.get("seed_product_id", f"{plant_id}_seed")
            amount = inventory_amount(player, seed_pid)
            rect = pygame.Rect(cx, cy, chip_w, chip_h)
            sel = plant_id == selected
            empty = amount < 1
            base = (235, 228, 215) if empty else (PANEL_BG_DARK if not sel else ACCENT_HOVER)
            pygame.draw.rect(screen, base, rect, border_radius=8)
            border_c = ACCENT if sel else PANEL_BORDER
            pygame.draw.rect(screen, border_c, rect, 2 if sel else 1, border_radius=8)
            draw_product_icon(screen, (rect.x + 12, rect.centery), seed_pid, 8)
            name = plant_crop_label(plant_id, plants_meta)
            if len(name) > 9:
                name = name[:8] + "…"
            prefix = f"{i + 1}·" if hotkey_index and i < 6 else ""
            screen.blit(
                fonts["tiny"].render(f"{prefix}{name}", True, TEXT_ON_DARK if sel else TEXT),
                (rect.x + 26, rect.y + 6),
            )
            screen.blit(
                fonts["tiny"].render("семена", True, TEXT_SOFT),
                (rect.x + 26, rect.y + 20),
            )
            cnt_color = OK if amount > 0 else TEXT_SOFT
            cnt = fonts["tiny"].render(f"×{amount}", True, cnt_color)
            screen.blit(cnt, (rect.right - cnt.get_width() - 6, rect.y + 22))
            self._rects.append((plant_id, rect))
        rows = (len(seeds) + cols - 1) // cols if seeds else 0
        return y + (rows * (chip_h + gap) if rows else chip_h) + 4


class ProductPicker:
    """Harvested goods and processed items (sell with V)."""

    def __init__(self) -> None:
        self._rects: list[tuple[str, pygame.Rect]] = []

    def clear(self) -> None:
        self._rects = []

    def hit(self, pos) -> str | None:
        for product_id, rect in self._rects:
            if rect.collidepoint(pos):
                return product_id
        return None

    def draw(
        self,
        screen,
        fonts,
        x: int,
        y: int,
        player: dict | None,
        selected: str | None,
        *,
        max_w: int = 320,
    ) -> int:
        self._rects = []
        gap = 6
        cols = max(1, min(2, (max_w + gap) // (100 + gap)))
        chip_w = (max_w - (cols - 1) * gap) // cols if cols else max_w
        chip_h = 36
        items = []
        if player:
            items = [
                i for i in player.get("inventory", [])
                if is_bag_product(i.get("product_id", "")) and int(i.get("amount", 0)) > 0
            ]
            items.sort(key=lambda i: product_label(i["product_id"]))
        if not items:
            screen.blit(
                fonts["tiny"].render("пусто — собери урожай", True, TEXT_SOFT),
                (x, y + 4),
            )
            return y + 28
        for i, item in enumerate(items[:8]):
            pid = item["product_id"]
            amt = int(item["amount"])
            col = i % cols
            row = i // cols
            rect = pygame.Rect(
                x + col * (chip_w + gap),
                y + row * (chip_h + gap),
                chip_w,
                chip_h,
            )
            sel = pid == selected
            pygame.draw.rect(
                screen,
                ACCENT_HOVER if sel else PANEL_BG_DARK,
                rect,
                border_radius=8,
            )
            pygame.draw.rect(screen, ACCENT if sel else PANEL_BORDER, rect, 2 if sel else 1, border_radius=8)
            draw_product_icon(screen, (rect.x + 12, rect.centery), pid, 8)
            name = product_label(pid)
            if len(name) > 8:
                name = name[:7] + "…"
            screen.blit(
                fonts["tiny"].render(name, True, TEXT_ON_DARK if sel else TEXT),
                (rect.x + 26, rect.y + 6),
            )
            screen.blit(
                fonts["tiny"].render(f"×{amt}", True, OK),
                (rect.x + 26, rect.y + 20),
            )
            self._rects.append((pid, rect))
        rows = (min(len(items), 8) + cols - 1) // cols
        return y + rows * (chip_h + gap) + 4


class RecipePicker:
    """Craft recipe selection (building must match player factories)."""

    def __init__(self) -> None:
        self._rects: list[tuple[str, pygame.Rect]] = []

    def clear(self) -> None:
        self._rects = []

    def hit(self, pos) -> str | None:
        for recipe_id, rect in self._rects:
            if rect.collidepoint(pos):
                return recipe_id
        return None

    def draw(
        self,
        screen,
        fonts,
        x: int,
        y: int,
        recipes: list[dict],
        selected: str,
        player: dict | None,
        factory_types: set[str],
        max_w: int,
    ) -> int:
        self._rects = []
        chip_w = 118
        chip_h = 32
        gap = 6
        cols = max(1, min(3, (max_w + gap) // (chip_w + gap)))
        shown = [
            r for r in recipes
            if r.get("building_type") in factory_types
        ]
        for i, recipe in enumerate(shown):
            rid = recipe["recipe_id"]
            col = i % cols
            row = i // cols
            cx = x + col * (chip_w + gap)
            cy = y + row * (chip_h + gap)
            rect = pygame.Rect(cx, cy, chip_w, chip_h)
            sel = rid == selected
            ok, _ = can_craft_recipe(player, recipe)
            base = ACCENT_HOVER if sel else (BTN_SECONDARY if ok else (220, 215, 208))
            pygame.draw.rect(screen, base, rect, border_radius=8)
            pygame.draw.rect(screen, ACCENT if sel else PANEL_BORDER, rect, 2, border_radius=8)
            out = recipe.get("output_product_id", rid)
            draw_product_icon(screen, (rect.x + 12, rect.centery), out, 7)
            name = recipe.get("output_display_name") or product_label(out)
            if len(name) > 10:
                name = name[:9] + "…"
            screen.blit(
                fonts["tiny"].render(name, True, TEXT_ON_DARK if sel else TEXT),
                (rect.x + 24, rect.y + 8),
            )
            self._rects.append((rid, rect))
        rows = (len(shown) + cols - 1) // cols if shown else 0
        return y + (rows * (chip_h + gap) if rows else 0) + 4


class AnimalPicker:
    def __init__(self) -> None:
        self._rects: list[tuple[str, pygame.Rect]] = []

    def clear(self) -> None:
        self._rects = []

    def hit(self, pos) -> str | None:
        for animal_id, rect in self._rects:
            if rect.collidepoint(pos):
                return animal_id
        return None

    def draw(
        self,
        screen,
        fonts,
        x: int,
        y: int,
        animals: list[dict],
        selected: str,
        money: int,
    ) -> int:
        self._rects = []
        chip_w = 118
        chip_h = 32
        gap = 6
        for i, animal in enumerate(animals):
            aid = animal["animal_id"]
            cx = x + (i % 2) * (chip_w + gap)
            cy = y + (i // 2) * (chip_h + gap)
            rect = pygame.Rect(cx, cy, chip_w, chip_h)
            sel = aid == selected
            price = int(animal.get("price", 0))
            can = money >= price
            pygame.draw.rect(
                screen,
                ACCENT_HOVER if sel else (BTN_SECONDARY if can else (210, 205, 198)),
                rect,
                border_radius=8,
            )
            pygame.draw.rect(screen, ACCENT if sel else PANEL_BORDER, rect, 2, border_radius=8)
            label = animal.get("display_name") or animal_label(aid)
            screen.blit(
                fonts["tiny"].render(f"{label} {price}B", True, TEXT_ON_DARK if sel else TEXT),
                (rect.x + 8, rect.y + 8),
            )
            self._rects.append((aid, rect))
        rows = (len(animals) + 1) // 2 if animals else 0
        return y + rows * (chip_h + gap) + 4


def draw_progress_bar(screen, rect, ratio: float, color, bg=(220, 210, 195)) -> None:
    pygame.draw.rect(screen, bg, rect, border_radius=4)
    inner = rect.copy()
    inner.w = max(0, int(rect.w * max(0, min(1, ratio))))
    if inner.w > 0:
        pygame.draw.rect(screen, color, inner, border_radius=4)


def inventory_amount(player: dict | None, product_id: str) -> int:
    if not player:
        return 0
    for item in player.get("inventory", []):
        if item.get("product_id") == product_id:
            return int(item.get("amount", 0))
    return 0


def can_craft_recipe(player: dict | None, recipe: dict) -> tuple[bool, list[str]]:
    if not player or not recipe:
        return False, []
    missing: list[str] = []
    for ing in recipe.get("ingredients") or []:
        need = int(ing.get("amount", 0))
        have = inventory_amount(player, ing.get("product_id", ""))
        if have < need:
            missing.append(f"{product_label(ing['product_id'])} ×{need - have}")
    return len(missing) == 0, missing


def draw_goal_progress(
    screen,
    fonts,
    rect: pygame.Rect,
    x: int,
    y: int,
    have: int,
    need: int,
    product_id: str,
) -> int:
    draw_product_icon(screen, (x + 6, y + 8), product_id, 8)
    label = product_label(product_id)
    screen.blit(fonts["small"].render(label, True, TEXT), (x + 22, y + 2))
    bar = pygame.Rect(x + 22, y + 20, min(rect.w - 54, 240), 10)
    ratio = min(1.0, have / need) if need > 0 else 0.0
    draw_progress_bar(screen, bar, ratio, GROWTH_READY if have >= need else ACCENT)
    screen.blit(
        fonts["tiny"].render(f"{have}/{need}", True, TEXT_SOFT),
        (bar.right + 8, y + 18),
    )
    if product_id in RECIPE_RU:
        screen.blit(
            fonts["tiny"].render(RECIPE_RU[product_id], True, TEXT_SOFT),
            (x, y + 34),
        )
        return y + 52
    return y + 36


def draw_money_badge(screen, fonts, x, y, amount: int) -> None:
    text = f"{amount} B"
    surf = fonts["body"].render(text, True, TEXT)
    pad_x, pad_y = 12, 6
    box = surf.get_rect()
    box.topleft = (x, y)
    box.w += pad_x * 2 + 22
    box.h += pad_y * 2
    pygame.draw.rect(screen, (40, 30, 15), box.move(0, 2), border_radius=16)
    pygame.draw.rect(screen, MONEY, box, border_radius=16)
    pygame.draw.rect(screen, MONEY_BORDER, box, 2, border_radius=16)
    coin = fonts["small"].render("◎", True, MONEY_BORDER)
    screen.blit(coin, (box.x + 8, box.y + 5))
    screen.blit(surf, (box.x + 26, box.y + pad_y))


def draw_shop_grid(
    screen,
    fonts,
    x: int,
    y: int,
    shop_items: list[tuple[str, int]],
    money: int,
    mouse_pos,
    buttons_out: list,
    *,
    max_w: int = 400,
) -> int:
    buttons_out.clear()
    gap = 6
    cols = 2
    btn_w = (max_w - gap) // cols
    btn_h = 30
    for i, (product_id, price) in enumerate(shop_items):
        col = i % cols
        row = i // cols
        btn_rect = pygame.Rect(x + col * (btn_w + gap), y + row * (btn_h + gap), btn_w, btn_h)
        btn = ShopButton(btn_rect, product_id, price)
        buttons_out.append(btn)
        btn.draw(screen, fonts, mouse_pos, money >= price)
    rows = (len(shop_items) + cols - 1) // cols if shop_items else 0
    return y + (rows * (btn_h + gap) if rows else 0) + 4


def draw_factories_compact(
    screen,
    fonts,
    x: int,
    y: int,
    factories: list[dict],
    owner_id: str,
    recipe_by_id,
    *,
    line_w: int = 400,
) -> int:
    labels = {"BAKERY": "Пекарня", "DAIRY": "Сыроварня", "MEAT": "Мясной цех"}
    mine = [f for f in factories if f.get("owner_player_id") == owner_id]
    if not mine:
        return y
    for f in mine:
        ftype = f.get("factory_type", "?")
        title = labels.get(ftype, ftype)
        active = f.get("active_recipe_id")
        rem = int(f.get("remaining_time_sec", 0))
        if active:
            out = product_label(
                recipe_by_id(active).get("output_product_id", active)
                if recipe_by_id(active)
                else active
            )
            line = f"{title}: {out} · {rem} т"
            color = ACCENT
        else:
            line = f"{title}: свободен"
            color = TEXT_SOFT
        screen.blit(fonts["tiny"].render(line, True, color), (x, y))
        y += 16
    return y + 4


def draw_win_overlay(screen, fonts, *, winner: str, you: str, target_product: str) -> None:
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((25, 35, 25, 200))
    screen.blit(overlay, (0, 0))
    won = winner == you
    if won:
        title, sub = "Победа!", f"Первым получил: {product_label(target_product)}"
        accent = OK
    else:
        title, sub = "Матч окончен", f"Победил: {winner}"
        accent = ACCENT
    box = pygame.Rect(WIDTH // 2 - 240, HEIGHT // 2 - 100, 480, 200)
    _shadow_rect(screen, box, radius=20, offset=5)
    pygame.draw.rect(screen, PANEL_BG, box, border_radius=20)
    pygame.draw.rect(screen, accent, box, 4, border_radius=20)
    screen.blit(fonts["title"].render(title, True, accent if won else TEXT), (box.x + 36, box.y + 40))
    screen.blit(fonts["body"].render(sub, True, TEXT), (box.x + 36, box.y + 92))
    screen.blit(
        fonts["small"].render("Esc — вернуться в меню", True, TEXT_SOFT),
        (box.x + 36, box.y + 138),
    )


def draw_lobby_hero(screen, fonts) -> None:
    hero = pygame.Rect(420, 88, WIDTH - 460, 200)
    _shadow_rect(screen, hero, radius=16)
    pygame.draw.rect(screen, PANEL_BG, hero, border_radius=16)
    pygame.draw.rect(screen, PANEL_BORDER, hero, 2, border_radius=16)
    screen.blit(fonts["title"].render("Добро пожаловать!", True, TEXT), (hero.x + 28, hero.y + 24))
    lines = [
        "Выращивай культуры, пеки хлеб и обгоняй соперника.",
        "Поливай грядки, следи за водой и используй саботаж.",
        "Победа — когда в сумке появится цель матча.",
    ]
    for i, line in enumerate(lines):
        screen.blit(fonts["body"].render(line, True, TEXT_SOFT), (hero.x + 28, hero.y + 72 + i * 28))


def draw_lobby_status(
    screen,
    fonts,
    *,
    in_room: bool,
    is_host: bool,
    join_code: str,
    server_ok: bool,
) -> None:
    x, y = 420, 300
    if server_ok:
        dot, label = OK, "Сервер доступен"
    else:
        dot, label = WARN, "Проверь подключение"
    pygame.draw.circle(screen, dot, (x, y + 8), 6)
    screen.blit(fonts["small"].render(label, True, TEXT_ON_DARK), (x + 16, y))
    y += 28
    if in_room:
        role = "Хост комнаты" if is_host else "В комнате — жди старт"
        screen.blit(fonts["body"].render(role, True, ACCENT_HOVER), (x, y))
        if join_code:
            code_box = pygame.Rect(x, y + 28, 200, 36)
            pygame.draw.rect(screen, PANEL_BG, code_box, border_radius=8)
            pygame.draw.rect(screen, ACCENT, code_box, 2, border_radius=8)
            screen.blit(fonts["title"].render(join_code, True, TEXT), (code_box.x + 16, code_box.y + 4))


def draw_lobby_roster(
    screen,
    fonts,
    *,
    players: list[dict],
    my_player_id: str | None,
    host_player_id: str | None = None,
    x: int = 420,
    y: int = 400,
) -> None:
    """Players currently in the room (lobby poll)."""
    box = pygame.Rect(x, y, WIDTH - x - 28, 120)
    _shadow_rect(screen, box, radius=12)
    pygame.draw.rect(screen, PANEL_BG, box, border_radius=12)
    pygame.draw.rect(screen, PANEL_BORDER, box, 2, border_radius=12)
    screen.blit(fonts["body"].render("В комнате", True, TEXT), (box.x + 16, box.y + 12))
    if not players:
        screen.blit(
            fonts["small"].render("Пока только ты — жди друзей", True, TEXT_SOFT),
            (box.x + 16, box.y + 44),
        )
        return
    row_y = box.y + 40
    for p in players:
        pid = p.get("player_id", "?")
        name = (p.get("display_name") or pid).strip()
        is_me = pid == my_player_id
        is_host = host_player_id is not None and pid == host_player_id
        tag = " (ты)" if is_me else ""
        host_mark = " ★" if is_host else ""
        color = ACCENT_HOVER if is_me else TEXT_ON_DARK
        line = f"{pid} · {name}{host_mark}{tag}"
        screen.blit(fonts["body"].render(line, True, color), (box.x + 16, row_y))
        row_y += 26
        if row_y > box.bottom - 8:
            screen.blit(fonts["small"].render("…", True, TEXT_SOFT), (box.x + 16, row_y))
            break


def draw_opponent_picker(
    screen,
    fonts,
    x: int,
    y: int,
    opponents: list[dict],
    selected_id: str | None,
) -> list[tuple[str, pygame.Rect]]:
    """
    Tabs to pick which opponent farm to view (3+ players).
    Returns (player_id, rect) for click handling.
    """
    hits: list[tuple[str, pygame.Rect]] = []
    if len(opponents) <= 1:
        return hits
    screen.blit(fonts["small"].render("Смотреть ферму:", True, TEXT_SOFT), (x, y))
    cx = x
    cy = y + 20
    for opp in opponents:
        pid = opp["player_id"]
        label = (opp.get("display_name") or pid).strip()
        if len(label) > 12:
            label = label[:11] + "…"
        surf = fonts["small"].render(label, True, TEXT)
        pad_x, pad_y = 12, 6
        w = surf.get_width() + pad_x * 2
        h = surf.get_height() + pad_y * 2
        rect = pygame.Rect(cx, cy, w, h)
        selected = pid == selected_id
        bg = ACCENT if selected else PANEL_BG
        border = ACCENT_HOVER if selected else PANEL_BORDER
        pygame.draw.rect(screen, bg, rect, border_radius=8)
        pygame.draw.rect(screen, border, rect, 2, border_radius=8)
        screen.blit(surf, (rect.x + pad_x, rect.y + pad_y))
        hits.append((pid, rect))
        cx += w + 8
    return hits


def tile_hint(tile: dict | None, selected_seed: str, my_player_id: str | None = None) -> str:
    if tile is None:
        return "Выбери грядку — кликни по клетке (своя или соперника)"
    if my_player_id and tile.get("owner_player_id") != my_player_id:
        flags = tile.get("flags") or []
        if "MINED" in flags:
            return "Клетка соперника · подозрительно (мина?)"
        return "Клетка соперника · саботаж (X)"
    if "MINED" in (tile.get("flags") or []):
        return "Мина на грядке — кликни, чтобы открыть сапёр"
    if tile.get("zone_type") == "ANIMAL":
        occ = tile.get("occupant_type", "EMPTY")
        if occ in (None, "EMPTY"):
            return "Пустой загон · купить корову (C)"
        name = animal_label(tile.get("occupant_id"))
        hunger = tile.get("hunger_ticks") or 0
        if hunger >= ANIMAL_HUNGER_STOP_TICKS:
            return f"{name} · голодна — покорми (F)"
        if hunger >= ANIMAL_HUNGER_WARN_TICKS:
            return f"{name} · пора кормить (F)"
        prod_elapsed = tile.get("production_elapsed_sec") or 0
        prod_needed = tile.get("production_interval_sec") or 0
        if prod_needed > 0:
            pct = min(100, int(prod_elapsed * 100 / prod_needed))
            return f"{name} · молоко {pct}% · корм (F)"
        return f"{name} · корм (F)"
    occ = tile.get("occupant_type", "EMPTY")
    water = tile.get("water_level")
    if occ == "EMPTY":
        return f"Пустая грядка · посадить: {product_label(selected_seed)} (T)"
    name = crop_label(tile.get("occupant_id"))
    growth_elapsed = tile.get("growth_elapsed_sec") or 0
    growth_needed = tile.get("growth_time_sec") or 0
    ripe = growth_needed > 0 and growth_elapsed >= growth_needed
    if ripe:
        return f"{name} · созрело — собери (H), лишнее продай (V)"
    if water is not None and water < WATER_LOW_THRESHOLD:
        if growth_needed > 0:
            pct = min(100, int(growth_elapsed * 100 / growth_needed))
            return f"{name} · рост {pct}% · нужен полив (W)"
        return f"{name} · нужен полив (W)"
    if growth_needed > 0:
        pct = min(100, int(growth_elapsed * 100 / growth_needed))
        return f"{name} · рост {pct}%"
    if water is not None and water >= WATER_LOW_THRESHOLD:
        return f"{name} · можно собирать (H)"
    return f"На грядке: {name}"


def draw_farm_tile(
    screen,
    fonts,
    rect: pygame.Rect,
    tile: dict,
    *,
    selected: bool,
    own: bool,
) -> None:
    empty = tile.get("occupant_type") in (None, "EMPTY")
    if not own:
        color = TILE_ENEMY if not empty else TILE_ENEMY_EMPTY
    elif tile.get("zone_type") == "ANIMAL":
        color = TILE_ANIMAL if not empty else TILE_ANIMAL_EMPTY
    else:
        color = TILE_EMPTY if empty else TILE_PLANT

    pygame.draw.rect(screen, (50, 35, 25), rect.move(2, 3), border_radius=10)
    pygame.draw.rect(screen, color, rect, border_radius=10)
    pygame.draw.rect(screen, SOIL, rect, 2, border_radius=10)

    if "MINED" in (tile.get("flags") or []):
        pygame.draw.rect(screen, (220, 50, 50), rect, 3, border_radius=10)

    if selected:
        pygame.draw.rect(screen, TILE_SEL, rect, 4, border_radius=10)
        glow = rect.inflate(10, 10)
        pygame.draw.rect(screen, TILE_SEL_GLOW, glow, 2, border_radius=14)

    if not empty:
        growth_needed = tile.get("growth_time_sec") or 0
        growth_elapsed = tile.get("growth_elapsed_sec") or 0
        if (
            own
            and tile.get("zone_type") != "ANIMAL"
            and growth_needed > 0
            and growth_elapsed >= growth_needed
        ):
            pulse = 3 + int(2 * abs((pygame.time.get_ticks() % 900) - 450) / 450)
            pygame.draw.rect(
                screen,
                GROWTH_READY,
                rect.inflate(pulse, pulse),
                3,
                border_radius=12,
            )
        if tile.get("zone_type") == "ANIMAL":
            occ_id = tile.get("occupant_id")
            if occ_id:
                draw_product_icon(screen, (rect.centerx, rect.y + 22), "milk", 11)
            label = animal_label(occ_id)
        else:
            plant_key = tile.get("occupant_id") or "wheat"
            for pid in PLANT_IDS:
                if pid in str(plant_key):
                    plant_key = pid
                    break
            draw_product_icon(screen, (rect.centerx, rect.y + 20), plant_key, 11)
            label = crop_label(tile.get("occupant_id"))
        surf = fonts["small"].render(label, True, TEXT_ON_DARK)
        screen.blit(surf, surf.get_rect(midtop=(rect.centerx, rect.y + 36)))

        if tile.get("zone_type") == "ANIMAL":
            hunger = tile.get("hunger_ticks") or 0
            if own and hunger >= ANIMAL_HUNGER_WARN_TICKS:
                pulse = 3 + int(2 * abs((pygame.time.get_ticks() % 900) - 450) / 450)
                border_color = (
                    HUNGER_CRITICAL
                    if hunger >= ANIMAL_HUNGER_STOP_TICKS
                    else HUNGER_LOW
                )
                pygame.draw.rect(
                    screen,
                    border_color,
                    rect.inflate(pulse, pulse),
                    3,
                    border_radius=12,
                )
            prod_elapsed = tile.get("production_elapsed_sec") or 0
            prod_needed = tile.get("production_interval_sec") or 0
            bar_y = rect.bottom - 14
            if prod_needed > 0 and hunger < ANIMAL_HUNGER_STOP_TICKS:
                ratio = min(1.0, prod_elapsed / prod_needed)
                bar = pygame.Rect(rect.x + 8, bar_y, rect.w - 16, 7)
                draw_progress_bar(screen, bar, ratio, MILK)
                bar_y -= 10
            if own and hunger >= ANIMAL_HUNGER_WARN_TICKS:
                hunger_ratio = min(1.0, hunger / float(ANIMAL_HUNGER_STOP_TICKS))
                hbar = pygame.Rect(rect.x + 8, bar_y, rect.w - 16, 7)
                hcolor = (
                    HUNGER_CRITICAL
                    if hunger >= ANIMAL_HUNGER_STOP_TICKS
                    else HUNGER_LOW
                )
                draw_progress_bar(screen, hbar, hunger_ratio, hcolor)
            return

        if growth_needed > 0:
            ratio = min(1.0, growth_elapsed / growth_needed)
            bar = pygame.Rect(rect.x + 8, rect.bottom - 26, rect.w - 16, 7)
            bar_color = GROWTH_READY if ratio >= 1.0 else GROWTH
            draw_progress_bar(screen, bar, ratio, bar_color)
        water = tile.get("water_level")
        if water is not None:
            ratio = min(1.0, water / 100.0)
            bar = pygame.Rect(rect.x + 8, rect.bottom - 14, rect.w - 16, 7)
            if water < WATER_CRITICAL_THRESHOLD:
                bar_color = WATER_CRITICAL
            elif water < WATER_LOW_THRESHOLD:
                bar_color = WATER_LOW
            else:
                bar_color = WATER_OK
            draw_progress_bar(screen, bar, ratio, bar_color)
            if own and water < WATER_LOW_THRESHOLD:
                pulse = 3 + int(2 * abs((pygame.time.get_ticks() % 900) - 450) / 450)
                border_color = (
                    WATER_CRITICAL
                    if water < WATER_CRITICAL_THRESHOLD
                    else WATER_LOW
                )
                pygame.draw.rect(
                    screen,
                    border_color,
                    rect.inflate(pulse, pulse),
                    3,
                    border_radius=12,
                )
    else:
        label = "загон" if tile.get("zone_type") == "ANIMAL" else "пусто"
        surf = fonts["small"].render(label, True, TEXT_SOFT)
        screen.blit(surf, surf.get_rect(center=rect.center))
