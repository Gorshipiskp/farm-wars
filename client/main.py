"""
Farm Wars pygame client — lobby + match UI.

Run:
    py tools/init_db.py --seed
    py -m server
    py -m client
"""

import argparse
import logging
import os

import pygame

from shared.log_config import setup_logging
from client.net import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    ServerClient,
    ServerError,
    parse_server_address,
)
from client.session import ClientSession
from client.sync_poller import SyncPoller
from client import ui

setup_logging()
log = logging.getLogger("farm_wars.client")

STATE_LOBBY = "lobby"
STATE_MATCH = "match"

SHOP_ITEMS = [
    ("wheat", 5),
    ("corn", 6),
    ("potato", 4),
    ("flour", 8),
]
SEED_IDS = ["wheat", "corn", "potato"]


class TextField:
    def __init__(self, rect, placeholder=""):
        self.rect = pygame.Rect(rect)
        self.text = ""
        self.placeholder = placeholder
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if not self.active:
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif len(self.text) < 24 and event.unicode.isprintable():
                self.text += event.unicode


class LobbyButton:
    def __init__(self, rect, label, primary=False):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.primary = primary

    def draw(self, screen, fonts, mouse):
        hover = self.rect.collidepoint(mouse)
        if self.primary:
            bg = ui.ACCENT_HOVER if hover else ui.ACCENT
            color = ui.TEXT_ON_DARK
        else:
            bg = ui.BTN_SECONDARY_HOVER if hover else ui.BTN_SECONDARY
            color = ui.TEXT
        pygame.draw.rect(screen, bg, self.rect, border_radius=10)
        surf = fonts["body"].render(self.label, True, color)
        screen.blit(surf, surf.get_rect(center=self.rect.center))

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)


class FarmWarsApp:
    def __init__(self, server_host: str = DEFAULT_HOST, server_port: int = DEFAULT_PORT):
        pygame.init()
        self.screen = pygame.display.set_mode((ui.WIDTH, ui.HEIGHT))
        pygame.display.set_caption("Farm Wars — ферма")
        self.clock = pygame.time.Clock()
        self.fonts = ui.load_fonts()

        self.session = ClientSession()
        self.state = STATE_LOBBY
        self.status_msg = "Подключись к серверу и создай матч или войди по коду"
        self.selected_tile_id: str | None = None
        self.selected_seed_id: str = "wheat"
        self._shop_buttons: list[ui.ShopButton] = []
        self._action_buttons: list[ui.ActionButton] = []
        self.toasts = ui.ToastManager()
        self._prev_events: list = []

        self.field_server = TextField((56, 168, 200, 40), "127.0.0.1")
        self.field_server.text = server_host
        self.field_port = TextField((270, 168, 90, 40), "8765")
        self.field_port.text = str(server_port)
        self.field_name = TextField((56, 248, 304, 40), "Твоё имя")
        self.field_code = TextField((56, 328, 304, 40), "Код комнаты")
        self.btn_connect = LobbyButton((56, 392, 150, 44), "Проверить связь")
        self.btn_create = LobbyButton((218, 392, 150, 44), "Создать матч", primary=True)
        self.btn_join = LobbyButton((56, 448, 150, 44), "Войти")
        self.btn_start = LobbyButton((218, 448, 150, 44), "Начать игру", primary=True)

        self._action_buttons = [
            ui.ActionButton((ui.FARM_X, 400, 175, 40), "Полить", "W", "water"),
            ui.ActionButton((ui.FARM_X + 185, 400, 175, 40), "Посадить", "T", "plant"),
            ui.ActionButton((ui.FARM_X, 448, 175, 40), "Собрать", "H", "harvest"),
            ui.ActionButton((ui.FARM_X + 185, 448, 175, 40), "Печь хлеб", "B", "bake"),
        ]

        self.net = ServerClient()
        self.poller = SyncPoller(self.net, self.session)
        self._refresh_net_client()

    def _refresh_net_client(self) -> str:
        base_url = parse_server_address(self.field_server.text, self.field_port.text)
        self.net = ServerClient(base_url)
        self.poller.stop()
        self.poller = SyncPoller(self.net, self.session)
        return base_url

    def _check_server(self) -> bool:
        try:
            base = self._refresh_net_client()
            health = self.net.health()
            shop = health.get("shop_handler")
            if shop not in ("immediate_v4", "immediate_v3", "immediate_v2"):
                self.status_msg = "Сервер устарел — перезапусти: py -m server"
                self.toasts.push(self.status_msg, "error")
                return False
            self.status_msg = f"Связь есть · {base}"
            self.toasts.push("Сервер отвечает — можно играть", "ok")
            self.session.clear_error()
            return True
        except ServerError as exc:
            self.status_msg = f"Сервер недоступен: {exc.message}"
            self.toasts.push(self.status_msg, "error")
            return False

    def run(self):
        self._check_server()
        running = True
        while running:
            mouse = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif self.state == STATE_LOBBY:
                    self._lobby_event(event)
                else:
                    self._match_event(event)

            ui.draw_gradient_bg(self.screen)
            if self.state == STATE_LOBBY:
                self._draw_lobby(mouse)
            else:
                self._draw_match(mouse)
            self.toasts.draw(self.screen, self.fonts["body"])
            pygame.display.flip()
            self.clock.tick(30)

        self.poller.stop()
        pygame.quit()

    def _lobby_event(self, event):
        self.field_server.handle_event(event)
        self.field_port.handle_event(event)
        self.field_name.handle_event(event)
        self.field_code.handle_event(event)
        if self.btn_connect.clicked(event):
            self._check_server()
        if self.btn_create.clicked(event):
            self._do_create()
        if self.btn_join.clicked(event):
            self._do_join()
        if self.btn_start.clicked(event):
            self._do_start()

    def _do_create(self):
        if not self._check_server():
            return
        name = self.field_name.text.strip() or "Фермер"
        try:
            res = self.net.create_match(name)
            self.session.player_name = name
            self.session.match_id = res["match_id"]
            self.session.player_id = "p1"
            self.session.join_code = res["join_code"]
            self.session.is_host = True
            self.field_code.text = res["join_code"]
            self.status_msg = f"Матч создан! Код для друзей: {res['join_code']}"
            self.toasts.push(self.status_msg, "ok")
            self.session.clear_error()
        except ServerError as exc:
            self.status_msg = exc.message
            self.toasts.push(self.status_msg, "error")

    def _do_join(self):
        if not self._check_server():
            return
        name = self.field_name.text.strip() or "Гость"
        code = self.field_code.text.strip().upper()
        if not code:
            self.status_msg = "Введи код комнаты"
            return
        try:
            res = self.net.join_match(code, name)
            self.session.player_name = name
            self.session.match_id = res["match_id"]
            self.session.player_id = res["player_id"]
            self.session.join_code = code
            self.session.is_host = False
            self.status_msg = f"Ты в комнате как {res['player_id']}. Жди старт от хоста."
            self.toasts.push("Успешно вошёл в матч", "ok")
            self.session.clear_error()
        except ServerError as exc:
            self.status_msg = exc.message
            self.toasts.push(self.status_msg, "error")

    def _do_start(self):
        if not self.session.match_id:
            self.status_msg = "Сначала создай матч или войди"
            return
        if not self._check_server():
            return
        try:
            self.net.start_match(self.session.match_id)
            self.state = STATE_MATCH
            self.poller.start()
            self._prev_events = []
            self.status_msg = "Удачной фермы!"
            self.toasts.push("Матч начался — удачи!", "ok")
            self.session.clear_error()
        except ServerError as exc:
            self.status_msg = exc.message
            self.toasts.push(self.status_msg, "error")

    def _draw_lobby(self, mouse):
        screen = self.screen
        fonts = self.fonts
        screen.blit(fonts["title"].render("Farm Wars", True, ui.TEXT_ON_DARK), (48, 36))
        screen.blit(
            fonts["body"].render("Собери урожай, испеки хлеб и победи первым", True, ui.TEXT_ON_DARK),
            (48, 72),
        )

        card = pygame.Rect(40, 108, 372, 370)
        ui.draw_panel(screen, card, "Подключение", fonts)
        ui.draw_text_field(screen, self.field_server, fonts, "Адрес сервера")
        ui.draw_text_field(screen, self.field_port, fonts, "Порт")
        ui.draw_text_field(screen, self.field_name, fonts, "Имя игрока")
        ui.draw_text_field(screen, self.field_code, fonts, "Код друзей")

        self.btn_connect.draw(screen, fonts, mouse)
        self.btn_create.draw(screen, fonts, mouse)
        self.btn_join.draw(screen, fonts, mouse)
        if self.session.is_host and self.session.match_id:
            self.btn_start.draw(screen, fonts, mouse)
            code = self.session.join_code
            hint = fonts["small"].render(f"Передай друзьям код:  {code}", True, ui.ACCENT)
            screen.blit(hint, (56, 502))

        steps = [
            "1. Проверить связь",
            "2. Создать матч или войти по коду",
            "3. Начать игру (хост)",
        ]
        for i, line in enumerate(steps):
            screen.blit(fonts["small"].render(line, True, ui.TEXT_ON_DARK), (420, 120 + i * 24))

        self._draw_status_bar(548, self.status_msg)

    def _match_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                self._send_water()
            elif event.key == pygame.K_t:
                self._send_place()
            elif event.key == pygame.K_b:
                self._send_recipe()
            elif event.key == pygame.K_h:
                self._send_harvest()
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                self._select_seed(event.key - pygame.K_1)
            elif event.key == pygame.K_ESCAPE:
                self.state = STATE_LOBBY
                self.poller.stop()
                self.status_msg = "Вышел в меню"
                self.toasts.push(self.status_msg, "info")

        if event.type == pygame.MOUSEBUTTONDOWN:
            for btn in self._shop_buttons:
                if btn.clicked(event):
                    self._send_buy(btn.product_id)
                    return
            for btn in self._action_buttons:
                if btn.clicked(event):
                    if btn.action_id == "water":
                        self._send_water()
                    elif btn.action_id == "plant":
                        self._send_place()
                    elif btn.action_id == "harvest":
                        self._send_harvest()
                    elif btn.action_id == "bake":
                        self._send_recipe()
                    return
            self._pick_tile(event.pos)

    def _pick_tile(self, pos):
        world, *_ = self.session.snapshot()
        if not world:
            return
        for tile in self._my_tiles(world):
            if self._tile_rect(tile).collidepoint(pos):
                self.selected_tile_id = tile["tile_id"]
                return

    def _my_tiles(self, world):
        pid = self.session.player_id
        return [t for t in world.get("map", {}).get("tiles", []) if t.get("owner_player_id") == pid]

    def _tile_rect(self, tile):
        my_tiles = self._my_tiles(self.session.world_state or {})
        try:
            index = next(i for i, t in enumerate(my_tiles) if t["tile_id"] == tile["tile_id"])
        except StopIteration:
            index = 0
        col = index % 3
        row = index // 3
        x = ui.FARM_X + col * (ui.TILE_SIZE + ui.TILE_GAP)
        y = ui.FARM_Y + row * (ui.TILE_SIZE + ui.TILE_GAP)
        return pygame.Rect(x, y, ui.TILE_SIZE, ui.TILE_SIZE)

    def _selected_tile(self, world) -> dict | None:
        if not world or not self.selected_tile_id:
            return None
        for t in self._my_tiles(world):
            if t["tile_id"] == self.selected_tile_id:
                return t
        return None

    def _feed_toasts(self, events: list) -> None:
        if events == self._prev_events:
            return
        if len(events) > len(self._prev_events):
            for ev in events[len(self._prev_events):]:
                msg = ui.humanize_event(ev)
                if msg:
                    et = ev.get("event_type", "")
                    kind = "ok"
                    if et in ("CONTRACT_ERROR",):
                        kind = "error"
                    elif et in ("RECIPE_REJECTED", "PURCHASE_FAILED", "HARVEST_FAILED"):
                        kind = "warn"
                    self.toasts.push(msg, kind)
        self._prev_events = list(events)

    def _send_action(self, action_type: str, payload: dict, ok_msg: str):
        if self.session.match_finished:
            self.toasts.push("Матч уже окончен", "info")
            return
        try:
            action = self.net.make_action(self.session.player_id, action_type, payload)
            self.net.submit_action(self.session.match_id, self.session.player_id, action)
            self.session.clear_error()
            self.status_msg = ok_msg
            self.toasts.push(ok_msg, "info")
        except ServerError as exc:
            self.session.set_error(exc.message)
            self.status_msg = exc.message
            self.toasts.push(exc.message, "error")

    def _send_water(self):
        if not self.selected_tile_id:
            self.toasts.push("Сначала выбери грядку", "warn")
            return
        self._send_action("WATER_PLANT", {"tile_id": self.selected_tile_id}, "Поливаем…")

    def _select_seed(self, index: int):
        if 0 <= index < len(SEED_IDS):
            self.selected_seed_id = SEED_IDS[index]
            self.toasts.push(f"Семена: {ui.product_label(self.selected_seed_id)}", "info")

    def _send_buy(self, product_id: str | None):
        if not product_id:
            return
        self._send_action(
            "BUY_PRODUCT",
            {"product_id": product_id, "amount": 1},
            f"Покупаем {ui.product_label(product_id)}…",
        )

    def _send_harvest(self):
        if not self.selected_tile_id:
            self.toasts.push("Сначала выбери грядку", "warn")
            return
        self._send_action("HARVEST_PLANT", {"tile_id": self.selected_tile_id}, "Собираем урожай…")

    def _send_place(self):
        if not self.selected_tile_id:
            self.toasts.push("Сначала выбери грядку", "warn")
            return
        plant_id = self._resolve_plant_for_place()
        if not plant_id:
            self.toasts.push("Нет семян — загляни в магазин", "warn")
            return
        self._send_action(
            "PLACE_ON_TILE",
            {"tile_id": self.selected_tile_id, "plant_id": plant_id},
            f"Сажаем {ui.product_label(plant_id)}…",
        )

    def _resolve_plant_for_place(self) -> str | None:
        world, *_ = self.session.snapshot()
        if not world:
            return None
        player = next(
            (p for p in world.get("players", []) if p["player_id"] == self.session.player_id),
            None,
        )
        if not player:
            return None
        amounts = {i["product_id"]: i["amount"] for i in player.get("inventory", [])}
        if amounts.get(self.selected_seed_id, 0) >= 1:
            return self.selected_seed_id
        for seed_id in SEED_IDS:
            if amounts.get(seed_id, 0) >= 1:
                return seed_id
        return None

    def _send_recipe(self):
        world, *_ = self.session.snapshot()
        if not world:
            return
        pid = self.session.player_id
        factory = next((f for f in world.get("factories", []) if f.get("owner_player_id") == pid), None)
        if not factory:
            self.toasts.push("Нет пекарни", "warn")
            return
        recipe = "bread"
        self._send_action(
            "START_RECIPE",
            {"factory_id": factory["factory_id"], "recipe_id": recipe},
            "Запускаем печь…",
        )

    def _draw_match(self, mouse):
        screen = self.screen
        fonts = self.fonts
        world, tick, events, err, finished = self.session.snapshot()
        self._feed_toasts(events)

        name = self.session.player_name or self.session.player_id
        screen.blit(fonts["title"].render(f"Привет, {name}!", True, ui.TEXT_ON_DARK), (ui.FARM_X, 20))

        if world:
            player = next(
                (p for p in world.get("players", []) if p["player_id"] == self.session.player_id),
                None,
            )
            money = player["money_bestiki"] if player else 0
            ui.draw_money_badge(screen, fonts, ui.PANEL_X - 150, 22, money)

            farm_card = pygame.Rect(ui.FARM_X - 8, ui.FARM_Y - 36, 380, 510)
            pygame.draw.rect(screen, ui.SOIL_LIGHT, farm_card, border_radius=14)
            pygame.draw.rect(screen, ui.SOIL, farm_card, 3, border_radius=14)
            screen.blit(fonts["body"].render("Твоя ферма", True, ui.TEXT_ON_DARK), (ui.FARM_X, ui.FARM_Y - 28))

            self._draw_tiles(world)
            tile = self._selected_tile(world)
            hint = ui.tile_hint(tile, self.selected_seed_id)
            hint_rect = pygame.Rect(ui.FARM_X, 368, 360, 28)
            pygame.draw.rect(screen, (255, 255, 250), hint_rect, border_radius=8)
            screen.blit(fonts["small"].render(hint, True, ui.TEXT), (hint_rect.x + 10, hint_rect.y + 6))

            for btn in self._action_buttons:
                btn.enabled = not finished
                btn.draw(screen, fonts, mouse)

            self._draw_bakery_status(world, fonts)

            self._draw_sidebar(world, tick, events, player, mouse, finished)
        else:
            screen.blit(fonts["body"].render("Загружаем поле…", True, ui.TEXT_ON_DARK), (ui.FARM_X, ui.FARM_Y))

        if finished and world:
            self._draw_win_overlay(world)
        elif err:
            self._draw_status_bar(ui.HEIGHT - 36, err, ui.ERROR)
        else:
            self._draw_status_bar(ui.HEIGHT - 36, self.status_msg, ui.TEXT_ON_DARK)

    def _draw_tiles(self, world):
        screen = self.screen
        fonts = self.fonts
        for tile in self._my_tiles(world):
            rect = self._tile_rect(tile)
            empty = tile.get("occupant_type") == "EMPTY"
            color = ui.TILE_EMPTY if empty else ui.TILE_PLANT
            pygame.draw.rect(screen, color, rect, border_radius=10)
            pygame.draw.rect(screen, ui.SOIL, rect, 2, border_radius=10)

            if tile["tile_id"] == self.selected_tile_id:
                pygame.draw.rect(screen, ui.TILE_SEL, rect, 4, border_radius=10)
                glow = rect.inflate(8, 8)
                pygame.draw.rect(screen, ui.TILE_SEL_GLOW, glow, 2, border_radius=12)

            if not empty:
                label = ui.crop_label(tile.get("occupant_id"))
                surf = fonts["small"].render(label, True, ui.TEXT_ON_DARK)
                screen.blit(surf, surf.get_rect(midtop=(rect.centerx, rect.y + 10)))
                growth_elapsed = tile.get("growth_elapsed_sec") or 0
                growth_needed = tile.get("growth_time_sec") or 0
                if growth_needed > 0:
                    ratio = min(1.0, growth_elapsed / growth_needed)
                    bar = pygame.Rect(rect.x + 8, rect.bottom - 28, rect.w - 16, 8)
                    bar_color = ui.GROWTH_READY if ratio >= 1.0 else ui.GROWTH
                    ui.draw_progress_bar(screen, bar, ratio, bar_color)
                water = tile.get("water_level")
                if water is not None:
                    ratio = min(1.0, water / 100.0)
                    bar = pygame.Rect(rect.x + 8, rect.bottom - 16, rect.w - 16, 8)
                    bar_color = ui.WATER_OK if water >= 50 else ui.WATER_LOW
                    ui.draw_progress_bar(screen, bar, ratio, bar_color)
            else:
                screen.blit(fonts["small"].render("пусто", True, ui.TEXT_SOFT), (rect.x + 24, rect.y + 30))

    def _draw_bakery_status(self, world, fonts):
        screen = self.screen
        pid = self.session.player_id
        factory = next((f for f in world.get("factories", []) if f.get("owner_player_id") == pid), None)
        if not factory:
            return
        x = ui.FARM_X
        y = 498
        active = factory.get("active_recipe_id")
        rem = factory.get("remaining_time_sec", 0)
        queue = factory.get("queue", [])
        if active:
            text = f"Пекарня: {ui.product_label(active)} — {rem} сек"
            color = ui.ACCENT
        elif queue:
            text = f"Пекарня: очередь из {len(queue)}"
            color = ui.WARN
        else:
            text = "Пекарня: свободна"
            color = ui.TEXT_SOFT
        surf = fonts["small"].render(text, True, color)
        screen.blit(surf, (x, y))
        if queue and not active:
            qnames = ", ".join(ui.product_label(q.get("recipe_id", "?")) for q in queue[:2])
            if len(queue) > 2:
                qnames += f" +{len(queue) - 2}"
            screen.blit(fonts["small"].render(qnames, True, ui.TEXT_SOFT), (x, y + 18))

    def _draw_sidebar(self, world, tick, events, player, mouse, finished):
        screen = self.screen
        fonts = self.fonts
        rect = pygame.Rect(ui.PANEL_X, 88, ui.PANEL_W, ui.HEIGHT - 110)
        ui.draw_panel(screen, rect, "Инвентарь и магазин", fonts)

        x = rect.x + 16
        y = rect.y + 48
        win = world.get("win_condition", {})
        goal = ui.product_label(win.get("target_product_id", "?"))
        screen.blit(fonts["body"].render(f"Цель: {goal}", True, ui.ACCENT), (x, y))
        y += 26
        target = win.get("target_product_id", "")
        if target in ui.RECIPE_RU:
            screen.blit(fonts["small"].render(f"Нужно: {ui.RECIPE_RU[target]}", True, ui.TEXT_SOFT), (x, y))
        y += 28

        screen.blit(fonts["small"].render("Семена (1/2/3):", True, ui.TEXT_SOFT), (x, y))
        y += 22
        for i, seed in enumerate(SEED_IDS):
            sel = seed == self.selected_seed_id
            label = f"  {'▸ ' if sel else '   '}{i + 1}. {ui.product_label(seed)}"
            color = ui.ACCENT if sel else ui.TEXT
            screen.blit(fonts["small"].render(label, True, color), (x, y))
            y += 20
        y += 8

        screen.blit(fonts["body"].render("Сумка:", True, ui.TEXT), (x, y))
        y += 24
        if player:
            inv = [i for i in player.get("inventory", []) if i.get("amount", 0) > 0]
            if inv:
                for item in inv[:8]:
                    line = f"  {ui.product_label(item['product_id'])}  ×{item['amount']}"
                    screen.blit(fonts["small"].render(line, True, ui.TEXT), (x, y))
                    y += 20
            else:
                screen.blit(fonts["small"].render("  пусто — сходи в магазин", True, ui.TEXT_SOFT), (x, y))
                y += 20
        y += 8

        pid = self.session.player_id
        for f in world.get("factories", []):
            if f.get("owner_player_id") != pid:
                continue
            screen.blit(fonts["body"].render("Пекарня:", True, ui.TEXT), (x, y))
            y += 22
            active = f.get("active_recipe_id")
            rem = f.get("remaining_time_sec", 0)
            if active:
                label = f"  ▸ {ui.product_label(active)}"
                screen.blit(fonts["small"].render(label, True, ui.ACCENT), (x, y))
                timer_text = f"{rem} сек"
                timer_w = fonts["small"].size(timer_text)[0]
                screen.blit(
                    fonts["small"].render(timer_text, True, ui.TEXT),
                    (x + rect.w - 32 - timer_w, y),
                )
                y += 18
                bar = pygame.Rect(x, y, rect.w - 32, 6)
                ui.draw_progress_bar(screen, bar, min(1.0, rem / 60.0), ui.ACCENT)
                y += 16
            else:
                screen.blit(fonts["small"].render("  простаивает", True, ui.TEXT_SOFT), (x, y))
                y += 20

            queue = f.get("queue", [])
            if queue:
                screen.blit(fonts["small"].render("  В очереди:", True, ui.TEXT_SOFT), (x, y))
                y += 18
                for qi, qitem in enumerate(queue[:3]):
                    qname = ui.product_label(qitem.get("recipe_id", "?"))
                    qdur = qitem.get("duration_sec", "?")
                    qline = f"    {qi + 1}. {qname} ({qdur}с)"
                    screen.blit(fonts["small"].render(qline, True, ui.TEXT), (x, y))
                    y += 18
                if len(queue) > 3:
                    screen.blit(
                        fonts["small"].render(f"    и ещё {len(queue) - 3}…", True, ui.TEXT_SOFT),
                        (x, y),
                    )
                    y += 18
        y += 10

        screen.blit(fonts["body"].render("Магазин:", True, ui.TEXT), (x, y))
        y += 26
        money = player["money_bestiki"] if player else 0
        self._shop_buttons = []
        for product_id, price in SHOP_ITEMS:
            btn_rect = pygame.Rect(x, y, rect.w - 32, 32)
            btn = ui.ShopButton(btn_rect, product_id, price)
            self._shop_buttons.append(btn)
            btn.draw(screen, fonts, mouse, money >= price)
            y += 36

        feed_y = rect.bottom - 20
        visible = events[-4:]
        for ev in reversed(visible):
            msg = ui.humanize_event(ev)
            if msg:
                feed_y -= 18
                screen.blit(fonts["small"].render(f"· {msg[:48]}", True, ui.TEXT), (x, feed_y))
        if visible:
            feed_y -= 24
            screen.blit(fonts["small"].render("Последние новости:", True, ui.TEXT_SOFT), (x, feed_y))

    def _draw_win_overlay(self, world):
        overlay = pygame.Surface((ui.WIDTH, ui.HEIGHT), pygame.SRCALPHA)
        overlay.fill((20, 30, 20, 180))
        self.screen.blit(overlay, (0, 0))
        win = world.get("win_condition", {})
        winner = win.get("winner_player_id", "?")
        you = self.session.player_id
        if winner == you:
            title, sub = "Победа!", "Ты первым испёк цель матча"
            color = ui.OK
        else:
            title, sub = "Матч окончен", f"Победил игрок {winner}"
            color = ui.TEXT_ON_DARK
        box = pygame.Rect(ui.WIDTH // 2 - 220, ui.HEIGHT // 2 - 90, 440, 180)
        pygame.draw.rect(self.screen, ui.PANEL_BG, box, border_radius=16)
        pygame.draw.rect(self.screen, color, box, 4, border_radius=16)
        self.screen.blit(self.fonts["title"].render(title, True, ui.ACCENT if winner == you else ui.TEXT), (
            box.x + 40, box.y + 36,
        ))
        self.screen.blit(self.fonts["body"].render(sub, True, ui.TEXT), (box.x + 40, box.y + 88))
        self.screen.blit(
            self.fonts["small"].render("Esc — вернуться в меню", True, ui.TEXT_SOFT),
            (box.x + 40, box.y + 128),
        )

    def _draw_status_bar(self, y: int, text: str, color=ui.TEXT_ON_DARK):
        surf = self.fonts["small"].render(text, True, color)
        self.screen.blit(surf, (48, y))


def main():
    parser = argparse.ArgumentParser(description="Farm Wars client")
    parser.add_argument("--host", default=os.environ.get("FARM_WARS_SERVER_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.environ.get("FARM_WARS_SERVER_PORT", str(DEFAULT_PORT))))
    args = parser.parse_args()
    try:
        FarmWarsApp(server_host=args.host, server_port=args.port).run()
    except pygame.error as exc:
        log.error("Pygame: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
