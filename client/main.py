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
import time

import pygame

from client.ui import HEIGHT
from shared.game_pacing import real_seconds_for_ticks
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
from client.minesweeper_ui import run_minesweeper_modal

setup_logging()
log = logging.getLogger("farm_wars.client")

STATE_LOBBY = "lobby"
STATE_MATCH = "match"

# Fallback until /api/health returns catalog (prices from SQLite).
DEFAULT_SHOP_ITEMS = [
    ("wheat", 5),
    ("corn", 6),
    ("potato", 4),
    ("tomato", 7),
    ("carrot", 5),
    ("flour", 8),
    ("feed", 3),
]
DEFAULT_COW_PRICE = 50
FALLBACK_SEED_IDS = ["wheat", "corn", "potato", "tomato", "carrot", "sunflower"]


class TextField:
    def __init__(self, rect, placeholder=""):
        self.rect = pygame.Rect(rect)
        self.text = ""
        self.placeholder = placeholder
        self.active = False

    def handle_event(self, event):
        if ui.is_left_click(event):
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
        return ui.is_left_click(event) and self.rect.collidepoint(event.pos)


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
        self._sabotage_click_targets: list[tuple[str, pygame.Rect]] = []
        self._shop_items: list[tuple[str, int]] = list(DEFAULT_SHOP_ITEMS)
        self._animal_items: list[dict] = []
        self._selected_animal_id: str = "cow"
        self._sabotage_items: list[dict] = []
        self._action_buttons: list[ui.ActionButton] = []
        self._recipes: list[dict] = []
        self._win_product_id: str = "bread"
        self._seed_ids: list[str] = list(FALLBACK_SEED_IDS)
        self._plants_meta: dict[str, dict] = {}
        self._selected_recipe_id: str = "bread"
        self._seed_picker = ui.SeedPicker()
        self._product_picker = ui.ProductPicker()
        self._recipe_picker = ui.RecipePicker()
        self._animal_picker = ui.AnimalPicker()
        self._selected_sell_product_id: str | None = None
        self._sidebar_rect: pygame.Rect | None = None
        self._server_ok = False
        self.toasts = ui.ToastManager()
        self._prev_events: list = []
        self._last_lobby_poll = 0.0
        self._awaiting_match_start = False
        self._lobby_players: list[dict] = []
        self._lobby_host_id: str | None = None
        self._view_opponent_id: str | None = None
        self._opponent_tab_rects: list[tuple[str, pygame.Rect]] = []

        self.field_server = TextField((56, 132, 200, 40), "127.0.0.1")
        self.field_server.text = server_host
        self.field_port = TextField((270, 132, 90, 40), "8765")
        self.field_port.text = str(server_port)
        self.field_name = TextField((56, 212, 304, 40), "Твоё имя")
        self.field_code = TextField((56, 292, 304, 40), "Код комнаты")
        self.btn_connect = LobbyButton((56, 356, 150, 44), "Проверить связь")
        self.btn_create = LobbyButton((218, 356, 150, 44), "Создать матч", primary=True)
        self.btn_join = LobbyButton((56, 412, 150, 44), "Войти")
        self.btn_start = LobbyButton((218, 412, 150, 44), "Начать игру", primary=True)

        self._action_buttons = [
            ui.ActionButton(pygame.Rect(0, 0, 1, 1), "Полить", "W", "water"),
            ui.ActionButton(pygame.Rect(0, 0, 1, 1), "Посадить", "T", "plant"),
            ui.ActionButton(pygame.Rect(0, 0, 1, 1), "Собрать", "H", "harvest"),
            ui.ActionButton(pygame.Rect(0, 0, 1, 1), "Печь", "B", "bake"),
            ui.ActionButton(pygame.Rect(0, 0, 1, 1), "Животное", "C", "buy_animal"),
            ui.ActionButton(pygame.Rect(0, 0, 1, 1), "Кормить", "F", "feed"),
            ui.ActionButton(pygame.Rect(0, 0, 1, 1), "Продать", "V", "sell"),
        ]

        self.net = ServerClient()
        self.poller = SyncPoller(self.net, self.session)
        self._refresh_net_client()

    def _apply_catalog_from_health(self, health: dict) -> None:
        catalog = health.get("catalog") or {}
        products = catalog.get("products") or []
        if products:
            self._shop_items = [(p["product_id"], int(p["price"])) for p in products]
        plants = catalog.get("plants") or []
        if plants:
            self._plants_meta = {p["plant_id"]: p for p in plants}
            self._seed_ids = [p["plant_id"] for p in plants]
        elif catalog.get("products"):
            self._seed_ids = [
                p["product_id"]
                for p in catalog["products"]
                if p["product_id"] in FALLBACK_SEED_IDS
            ]
        self._animal_items = list(catalog.get("animals") or [])
        if self._animal_items and self._selected_animal_id not in {
            a["animal_id"] for a in self._animal_items
        }:
            self._selected_animal_id = self._animal_items[0]["animal_id"]
        self._sabotage_items = list(catalog.get("sabotages") or [])
        self._recipes = list(catalog.get("recipes") or [])
        win = catalog.get("win_product_id")
        if win:
            self._win_product_id = win
        if self._recipes and self._selected_recipe_id not in {
            r["recipe_id"] for r in self._recipes
        }:
            self._selected_recipe_id = self._recipes[0]["recipe_id"]

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
            if shop not in (
                "immediate_v7",
                "immediate_v6",
                "immediate_v5",
                "immediate_v4",
                "immediate_v3",
                "immediate_v2",
            ):
                self.status_msg = "Сервер устарел — перезапусти: py -m server"
                self.toasts.push(self.status_msg, "error")
                return False
            self._apply_catalog_from_health(health)
            self._server_ok = True
            self.status_msg = f"Связь есть · {base}"
            self.toasts.push("Сервер отвечает — можно играть", "ok")
            self.session.clear_error()
            return True
        except ServerError as exc:
            self._server_ok = False
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
                self._poll_lobby_updates()
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
            self._awaiting_match_start = True
            self._lobby_players = [{"player_id": "p1", "display_name": name}]
            self.field_code.text = res["join_code"]
            self._refresh_lobby_roster()
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
            self._awaiting_match_start = True
            self._refresh_lobby_roster()
            self.status_msg = f"Ты в комнате как {res['player_id']}. Жди старт от хоста."
            self.toasts.push("Успешно вошёл в матч", "ok")
            self.session.clear_error()
        except ServerError as exc:
            self.status_msg = exc.message
            self.toasts.push(self.status_msg, "error")

    def _enter_match(self, initial_sync: dict | None = None) -> None:
        self._awaiting_match_start = False
        self._lobby_players = []
        self._view_opponent_id = None
        self.state = STATE_MATCH
        self.session.enable_sync()
        if initial_sync:
            self.session.apply_sync(initial_sync)
        self.poller.start()
        self._prev_events = []
        self.status_msg = "Удачной фермы!"
        self.toasts.push("Матч начался — удачи!", "ok")
        self.session.clear_error()

    def _leave_match_to_lobby(self) -> None:
        self.state = STATE_LOBBY
        self._awaiting_match_start = False
        self._view_opponent_id = None
        self.poller.stop()
        self.session.discard_live_state()
        self._prev_events = []
        self.status_msg = "Вышел в меню"
        self.toasts.push(self.status_msg, "info")

    def _refresh_lobby_roster(self) -> None:
        if not self.session.match_id:
            return
        try:
            roster = self.net.poll_roster(self.session.match_id)
            self._lobby_players = roster.get("players", [])
            self._lobby_host_id = roster.get("host_player_id")
        except ServerError:
            pass

    def _poll_lobby_updates(self) -> None:
        """Lobby: roster for everyone; sync poll for guests waiting for start."""
        if not self.session.match_id:
            return
        now = time.time()
        if now - self._last_lobby_poll < 0.35:
            return
        self._last_lobby_poll = now
        self._refresh_lobby_roster()
        if not self._awaiting_match_start or self.session.is_host:
            return
        try:
            sync = self.net.poll_sync(self.session.match_id, 0)
        except ServerError as exc:
            if exc.error_code == "NO_SYNC":
                return
            return
        if sync.get("world_state"):
            self._enter_match(initial_sync=sync)

    def _do_start(self):
        if not self.session.match_id:
            self.status_msg = "Сначала создай матч или войди"
            return
        if not self._check_server():
            return
        try:
            self.net.start_match(self.session.match_id)
            self._enter_match()
        except ServerError as exc:
            self.status_msg = exc.message
            self.toasts.push(self.status_msg, "error")

    def _draw_lobby(self, mouse):
        screen = self.screen
        fonts = self.fonts
        ui.draw_match_header(
            screen,
            fonts,
            player_name="Лобби",
            money=0,
            tick=0,
        )

        card = pygame.Rect(40, 72, 372, 400)
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

        ui.draw_lobby_hero(screen, fonts)
        ui.draw_lobby_status(
            screen,
            fonts,
            in_room=bool(self.session.match_id),
            is_host=self.session.is_host,
            join_code=self.session.join_code,
            server_ok=self._server_ok,
        )
        if self.session.match_id:
            ui.draw_lobby_roster(
                screen,
                fonts,
                players=self._lobby_players,
                my_player_id=self.session.player_id,
                host_player_id=self._lobby_host_id,
            )
        ui.draw_status_pill(screen, fonts, HEIGHT - 52, self.status_msg, ok=self._server_ok)

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
            elif event.key == pygame.K_c:
                self._send_buy_animal()
            elif event.key == pygame.K_f:
                self._send_feed()
            elif event.key == pygame.K_x:
                self._send_sabotage("poison_water")
            elif event.key == pygame.K_v:
                self._send_sell()
            elif event.key in (
                pygame.K_1, pygame.K_2, pygame.K_3,
                pygame.K_4, pygame.K_5, pygame.K_6,
            ):
                self._select_seed(event.key - pygame.K_1)
            elif event.key == pygame.K_ESCAPE:
                self._leave_match_to_lobby()

        if ui.is_left_click(event):
            for opp_id, rect in self._opponent_tab_rects:
                if rect.collidepoint(event.pos):
                    self._view_opponent_id = opp_id
                    tile = self._selected_tile(self.session.world_state)
                    if tile and tile.get("owner_player_id") != opp_id:
                        self.selected_tile_id = None
                    return
            recipe_id = self._recipe_picker.hit(event.pos)
            if recipe_id:
                self._selected_recipe_id = recipe_id
                self.toasts.push(f"Рецепт: {ui.product_label(self._recipe_output_id(recipe_id))}", "info")
                return
            animal_id = self._animal_picker.hit(event.pos)
            if animal_id:
                self._selected_animal_id = animal_id
                self.toasts.push(f"Животное: {ui.animal_label(animal_id)}", "info")
                return
            seed = self._seed_picker.hit(event.pos)
            if seed:
                self._select_seed_by_id(seed)
                return
            product_id = self._product_picker.hit(event.pos)
            if product_id:
                self._selected_sell_product_id = product_id
                self.toasts.push(
                    f"Продажа: {ui.product_label(product_id)} (V)",
                    "info",
                )
                return
            for sab_id, rect in self._sabotage_click_targets:
                if rect.collidepoint(event.pos):
                    self._send_sabotage(sab_id)
                    return
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
                    elif btn.action_id == "buy_animal":
                        self._send_buy_animal()
                    elif btn.action_id == "feed":
                        self._send_feed()
                    elif btn.action_id == "sell":
                        self._send_sell()
                    return
            self._pick_tile(event.pos)

    def _pick_tile(self, pos):
        world, *_ = self.session.snapshot()
        if not world:
            return
        my_tiles = self._my_tiles(world)
        enemy_tiles = self._viewed_opponent_tiles(world)
        for index, tile in enumerate(my_tiles):
            if self._tile_rect_at(index, ui.FARM_Y).collidepoint(pos):
                if "MINED" in (tile.get("flags") or []):
                    self.selected_tile_id = tile["tile_id"]
                    result = run_minesweeper_modal(self.screen, self.fonts)
                    if result == "win":
                        self._send_action(
                            "CLEAR_MINE",
                            {"tile_id": tile["tile_id"]},
                            "Мина обезврежена!",
                        )
                    return
                self.selected_tile_id = tile["tile_id"]
                return
        base_y = self._opponent_farm_y(world)
        for index, tile in enumerate(enemy_tiles):
            if self._tile_rect_at(index, base_y).collidepoint(pos):
                self.selected_tile_id = tile["tile_id"]
                return

    def _my_tiles(self, world):
        return self._tiles_for_owner(world, self.session.player_id)

    def _opponents(self, world) -> list[dict]:
        pid = self.session.player_id
        return [p for p in world.get("players", []) if p.get("player_id") != pid]

    def _ensure_view_opponent(self, world) -> None:
        opps = self._opponents(world)
        if not opps:
            self._view_opponent_id = None
            return
        ids = {p["player_id"] for p in opps}
        if self._view_opponent_id not in ids:
            self._view_opponent_id = opps[0]["player_id"]

    def _tiles_for_owner(self, world, owner_id: str) -> list[dict]:
        tiles = [
            t
            for t in world.get("map", {}).get("tiles", [])
            if t.get("owner_player_id") == owner_id
        ]
        tiles.sort(
            key=lambda t: (
                0 if t.get("zone_type") == "PLANT" else 1,
                t["tile_id"],
            )
        )
        return tiles

    def _viewed_opponent_tiles(self, world) -> list[dict]:
        self._ensure_view_opponent(world)
        if not self._view_opponent_id:
            return []
        return self._tiles_for_owner(world, self._view_opponent_id)

    def _viewed_opponent_name(self, world) -> str:
        if not self._view_opponent_id:
            return "соперника"
        for p in self._opponents(world):
            if p["player_id"] == self._view_opponent_id:
                return (p.get("display_name") or p["player_id"]).strip()
        return self._view_opponent_id

    def _tile_rect_at(self, index: int, base_y: int) -> pygame.Rect:
        col = index % ui.FARM_COLS
        row = index // ui.FARM_COLS
        x = ui.FARM_X + col * (ui.TILE_SIZE + ui.TILE_GAP)
        y = base_y + row * (ui.TILE_SIZE + ui.TILE_GAP)
        return pygame.Rect(x, y, ui.TILE_SIZE, ui.TILE_SIZE)

    def _tile_rect(self, tile):
        world = self.session.world_state or {}
        my_tiles = self._my_tiles(world)
        enemy_tiles = self._viewed_opponent_tiles(world)
        for index, t in enumerate(my_tiles):
            if t["tile_id"] == tile["tile_id"]:
                return self._tile_rect_at(index, ui.FARM_Y)
        base_y = self._opponent_farm_y(world)
        for index, t in enumerate(enemy_tiles):
            if t["tile_id"] == tile["tile_id"]:
                return self._tile_rect_at(index, base_y)
        return self._tile_rect_at(0, ui.FARM_Y)

    def _selected_tile(self, world) -> dict | None:
        if not world or not self.selected_tile_id:
            return None
        for t in world.get("map", {}).get("tiles", []):
            if t["tile_id"] == self.selected_tile_id:
                return t
        return None

    def _is_enemy_tile(self, tile: dict | None) -> bool:
        if not tile:
            return False
        return tile.get("owner_player_id") != self.session.player_id

    def _feed_toasts(self, events: list) -> None:
        if events == self._prev_events:
            return
        if len(events) > len(self._prev_events):
            for ev in events[len(self._prev_events):]:
                pl = ev.get("payload") or {}
                if (
                    ev.get("event_type") == "SABOTAGE_APPLIED"
                    and pl.get("is_hidden")
                    and pl.get("player_id") != self.session.player_id
                ):
                    continue
                ev_player = pl.get("player_id")
                if ev_player and ev_player != self.session.player_id:
                    if ev.get("event_type") in (
                        "CONTRACT_ERROR",
                        "HARVEST_FAILED",
                        "FEED_FAILED",
                        "RECIPE_REJECTED",
                        "PURCHASE_FAILED",
                        "SELL_FAILED",
                        "ANIMAL_PURCHASE_FAILED",
                        "SABOTAGE_FAILED",
                    ):
                        continue
                msg = ui.humanize_event(ev)
                if msg:
                    et = ev.get("event_type", "")
                    kind = "ok"
                    if et in ("CONTRACT_ERROR",):
                        kind = "error"
                    elif et in (
                        "RECIPE_REJECTED",
                        "PURCHASE_FAILED",
                        "HARVEST_FAILED",
                        "FEED_FAILED",
                        "ANIMAL_PURCHASE_FAILED",
                    ):
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
        if 0 <= index < len(self._seed_ids):
            self.selected_seed_id = self._seed_ids[index]
            self.toasts.push(
                f"Семена: {ui.seed_label_for_plant(self.selected_seed_id, self._plants_meta)}",
                "info",
            )

    def _select_seed_by_id(self, seed_id: str) -> None:
        if seed_id in self._seed_ids:
            self.selected_seed_id = seed_id
            self.toasts.push(
                f"Семена: {ui.seed_label_for_plant(seed_id, self._plants_meta)}",
                "info",
            )

    def _seed_product_id(self, plant_id: str) -> str:
        meta = self._plants_meta.get(plant_id, {})
        return meta.get("seed_product_id", f"{plant_id}_seed")

    def _recipe_output_id(self, recipe_id: str) -> str:
        for recipe in self._recipes:
            if recipe.get("recipe_id") == recipe_id:
                return recipe.get("output_product_id", recipe_id)
        return recipe_id

    def _factory_types(self, world: dict) -> set[str]:
        pid = self.session.player_id
        return {
            f["factory_type"]
            for f in world.get("factories", [])
            if f.get("owner_player_id") == pid
        }

    def _factory_for_recipe(self, world: dict, recipe_id: str) -> dict | None:
        recipe = next((r for r in self._recipes if r.get("recipe_id") == recipe_id), None)
        if not recipe:
            return None
        btype = recipe.get("building_type")
        pid = self.session.player_id
        return next(
            (
                f
                for f in world.get("factories", [])
                if f.get("owner_player_id") == pid and f.get("factory_type") == btype
            ),
            None,
        )

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

    def _send_buy_animal(self):
        world, *_ = self.session.snapshot()
        tile = self._selected_tile(world) if world else None
        if tile is None:
            self.toasts.push("Выбери загон (клетку снизу)", "warn")
            return
        if tile.get("zone_type") != "ANIMAL":
            self.toasts.push("Животное можно купить только в загоне", "warn")
            return
        if tile.get("occupant_type") not in (None, "EMPTY"):
            self.toasts.push("Загон занят", "warn")
            return
        animal_id = self._selected_animal_id or "cow"
        self._send_action(
            "BUY_ANIMAL",
            {"tile_id": self.selected_tile_id, "animal_id": animal_id},
            f"Покупаем {ui.animal_label(animal_id)}…",
        )

    def _send_sabotage(self, sabotage_id: str):
        world, *_ = self.session.snapshot()
        tile = self._selected_tile(world) if world else None
        if tile is None:
            self.toasts.push("Выбери клетку соперника", "warn")
            return
        if not self._is_enemy_tile(tile):
            self.toasts.push("Саботаж только по ферме соперника", "warn")
            return
        self._send_action(
            "APPLY_SABOTAGE",
            {"sabotage_id": sabotage_id, "target_tile_id": self.selected_tile_id},
            "Саботаж…",
        )

    def _send_feed(self):
        world, *_ = self.session.snapshot()
        tile = self._selected_tile(world) if world else None
        if tile is None:
            self.toasts.push("Выбери загон с коровой", "warn")
            return
        if tile.get("occupant_type") != "ANIMAL":
            self.toasts.push("Здесь нет животного", "warn")
            return
        animal_id = tile.get("occupant_id") or self._selected_animal_id or "cow"
        self._send_action(
            "FEED_ANIMAL",
            {"tile_id": self.selected_tile_id},
            f"Кормим {ui.animal_label(animal_id)}…",
        )

    def _send_place(self):
        if not self.selected_tile_id:
            self.toasts.push("Сначала выбери грядку", "warn")
            return
        plant_id = self._resolve_plant_for_place()
        if not plant_id:
            self.toasts.push("Нет семян — загляни в магазин", "warn")
            return
        crop = self._plants_meta.get(plant_id, {}).get("crop_display_name")
        crop_name = crop or ui.product_label(plant_id)
        self._send_action(
            "PLACE_ON_TILE",
            {"tile_id": self.selected_tile_id, "plant_id": plant_id},
            f"Сажаем {crop_name}…",
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
        if ui.inventory_amount(player, self._seed_product_id(self.selected_seed_id)) >= 1:
            return self.selected_seed_id
        for plant_id in self._seed_ids:
            if ui.inventory_amount(player, self._seed_product_id(plant_id)) >= 1:
                return plant_id
        return None

    def _send_sell(self) -> None:
        world, *_ = self.session.snapshot()
        if not world:
            return
        player = next(
            (p for p in world.get("players", []) if p["player_id"] == self.session.player_id),
            None,
        )
        if not player:
            return
        product_id = self._selected_sell_product_id
        if product_id and ui.inventory_amount(player, product_id) < 1:
            product_id = None
        if not product_id:
            for item in player.get("inventory", []):
                pid = item.get("product_id", "")
                if not ui.is_bag_product(pid):
                    continue
                if int(item.get("amount", 0)) > 0:
                    product_id = pid
                    break
        if not product_id:
            self.toasts.push("Нечего продать — сначала собери урожай", "warn")
            return
        self._send_action(
            "SELL_PRODUCT",
            {"product_id": product_id, "amount": 1},
            f"Продаём {ui.product_label(product_id)}…",
        )

    def _recipe_by_id(self, recipe_id: str) -> dict | None:
        return next((r for r in self._recipes if r.get("recipe_id") == recipe_id), None)

    def _send_recipe(self):
        world, *_ = self.session.snapshot()
        if not world:
            return
        recipe_id = self._selected_recipe_id or "bread"
        factory = self._factory_for_recipe(world, recipe_id)
        if not factory:
            self.toasts.push("Нет завода для этого рецепта", "warn")
            return
        label = ui.product_label(self._recipe_output_id(recipe_id))
        self._send_action(
            "START_RECIPE",
            {"factory_id": factory["factory_id"], "recipe_id": recipe_id},
            f"Готовим {label}…",
        )

    def _draw_match(self, mouse):
        screen = self.screen
        fonts = self.fonts
        world, tick, events, err, finished = self.session.snapshot()
        self._feed_toasts(events)

        name = self.session.player_name or self.session.player_id
        player = None
        money = 0
        if world:
            player = next(
                (p for p in world.get("players", []) if p["player_id"] == self.session.player_id),
                None,
            )
            money = player["money_bestiki"] if player else 0

        ui.draw_match_header(
            screen,
            fonts,
            player_name=name,
            money=money,
            tick=tick,
            join_code=self.session.join_code,
            is_host=self.session.is_host,
        )

        if world:
            card_w = ui.farm_panel_inner_width() + 20
            farm_card = pygame.Rect(ui.FARM_X - 10, ui.FARM_Y - 40, card_w, int(ui.FARM_PANEL_H))
            ui.draw_farm_card(screen, farm_card)
            ui.draw_zone_label(screen, fonts, ui.FARM_X, ui.FARM_Y - 32, "Твоя ферма")

            self._draw_farms(world)
            tile = self._selected_tile(world)
            hint = ui.tile_hint(tile, self.selected_seed_id, self.session.player_id)
            hint_rect = pygame.Rect(ui.FARM_X, ui.HINT_Y, card_w - 16, 28)
            ui.draw_hint_bar(screen, fonts, hint_rect, hint)

            self._draw_bakery_status(world, fonts)
            ui.draw_hotkey_bar(screen, fonts, ui.FARM_X, ui.HOTKEY_BAR_Y, card_w - 16)

            self._draw_sidebar(world, tick, events, player, mouse, finished)
        else:
            screen.blit(fonts["body"].render("Загружаем поле…", True, ui.TEXT_ON_DARK), (ui.FARM_X, ui.FARM_Y))

        if finished and world:
            win = world.get("win_condition", {})
            ui.draw_win_overlay(
                screen,
                fonts,
                winner=win.get("winner_player_id", "?"),
                you=self.session.player_id,
                target_product=win.get("target_product_id", self._win_product_id),
            )
        elif err:
            ui.draw_status_pill(screen, fonts, ui.HEIGHT - 52, err, ok=False)
        elif self.status_msg:
            ui.draw_status_pill(screen, fonts, ui.HEIGHT - 52, self.status_msg, ok=True)

    def _opponent_farm_y(self, world) -> int:
        return (
            ui.OPPONENT_FARM_Y_MULTI
            if len(self._opponents(world)) > 1
            else ui.OPPONENT_FARM_Y_SINGLE
        )

    def _draw_farms(self, world):
        opponents = self._opponents(world)
        enemy_tiles = self._viewed_opponent_tiles(world)
        farm_y = self._opponent_farm_y(world)
        if opponents:
            if len(opponents) > 1:
                self._opponent_tab_rects = ui.draw_opponent_picker(
                    self.screen,
                    self.fonts,
                    ui.FARM_X,
                    ui.OPPONENT_PICKER_Y,
                    opponents,
                    self._view_opponent_id,
                )
                label_y = ui.OPPONENT_LABEL_Y_MULTI
            else:
                self._opponent_tab_rects = []
                label_y = ui.OPPONENT_LABEL_Y_SINGLE
            opp_name = self._viewed_opponent_name(world)
            ui.draw_zone_label(
                self.screen,
                self.fonts,
                ui.FARM_X,
                label_y,
                f"Ферма: {opp_name}",
                enemy=True,
            )
        else:
            self._opponent_tab_rects = []
        self._draw_tile_group(world, self._my_tiles(world), ui.FARM_Y, own=True)
        if enemy_tiles:
            self._draw_tile_group(world, enemy_tiles, farm_y, own=False)

    def _draw_tile_group(self, world, tiles, base_y: int, own: bool):
        for index, tile in enumerate(tiles):
            rect = self._tile_rect_at(index, base_y)
            ui.draw_farm_tile(
                self.screen,
                self.fonts,
                rect,
                tile,
                selected=tile["tile_id"] == self.selected_tile_id,
                own=own,
            )

    def _draw_bakery_status(self, world, fonts):
        pid = self.session.player_id
        busy = [
            f for f in world.get("factories", [])
            if f.get("owner_player_id") == pid and f.get("active_recipe_id")
        ]
        if busy:
            f0 = busy[0]
            active = f0.get("active_recipe_id")
            rem = f0.get("remaining_time_sec", 0)
            text = f"Готовим: {ui.product_label(active)} · {int(real_seconds_for_ticks(rem))} с"
            ui.draw_bakery_chip(self.screen, fonts, ui.FARM_X, ui.BAKERY_Y, text, active=True)
        else:
            ui.draw_bakery_chip(
                self.screen, fonts, ui.FARM_X, ui.BAKERY_Y, "Заводы свободны", active=False
            )

    def _draw_sidebar_actions(
        self,
        screen: pygame.Surface,
        fonts: dict,
        x: int,
        y: int,
        mouse,
        finished: bool,
    ) -> int:
        bw = ui.SIDEBAR_ACTION_BTN_W
        bh = ui.SIDEBAR_ACTION_BTN_H
        gap = ui.SIDEBAR_ACTION_GAP
        col2 = x + bw + gap
        for i, btn in enumerate(self._action_buttons):
            col = i % 2
            row = i // 2
            btn.rect = pygame.Rect(
                x + col * (bw + gap),
                y + row * (bh + gap),
                bw,
                bh,
            )
            btn.enabled = not finished
            btn.draw(screen, fonts, mouse, compact=True)
        rows = (len(self._action_buttons) + 1) // 2
        return y + rows * (bh + gap)

    def _sync_sell_selection(self, player: dict | None) -> None:
        if not player:
            self._selected_sell_product_id = None
            return
        if self._selected_sell_product_id:
            if ui.inventory_amount(player, self._selected_sell_product_id) > 0:
                return
        for item in player.get("inventory", []):
            pid = item.get("product_id", "")
            if ui.is_bag_product(pid) and int(item.get("amount", 0)) > 0:
                self._selected_sell_product_id = pid
                return
        self._selected_sell_product_id = None

    def _draw_sidebar(self, world, tick, events, player, mouse, finished):
        screen = self.screen
        fonts = self.fonts
        rect = pygame.Rect(ui.PANEL_X, 64, ui.PANEL_W, ui.HEIGHT - 80)
        self._sidebar_rect = rect
        ui.draw_panel(screen, rect, "Ферма и склад", fonts)

        x = rect.x + 16
        inner_w = rect.w - 32
        y = rect.y + 48
        self._sync_sell_selection(player)

        win = world.get("win_condition", {})
        target = win.get("target_product_id") or self._win_product_id
        y = ui.draw_section_header(
            screen, fonts, x, y, f"Цель — {ui.product_label(target)}", line_w=inner_w
        )
        have_goal = ui.inventory_amount(player, target)
        y = ui.draw_goal_progress(screen, fonts, rect, x, y, have_goal, 1, target)

        y = ui.draw_section_header(
            screen, fonts, x, y, "Действия", line_w=inner_w
        )
        y = self._draw_sidebar_actions(screen, fonts, x, y, mouse, finished)
        y += 4

        craft_recipe = self._recipe_by_id(self._selected_recipe_id)
        if craft_recipe and player:
            ok, missing = ui.can_craft_recipe(player, craft_recipe)
            out = ui.product_label(craft_recipe.get("output_product_id", "bread"))
            chip_text = f"✓ Можно: {out} (B)" if ok else f"Нужно: {', '.join(missing)}"
            chip_color = ui.OK if ok else ui.TEXT_SOFT
            screen.blit(fonts["tiny"].render(chip_text, True, chip_color), (x, y))
            y += 18

        col_gap = 16
        col_w = (inner_w - col_gap) // 2
        row_top = y
        x_right = x + col_w + col_gap

        y = ui.draw_section_header(
            screen,
            fonts,
            x,
            row_top,
            "Урожай",
            "клик · продажа V",
            line_w=col_w,
        )
        y_products = self._product_picker.draw(
            screen,
            fonts,
            x,
            y,
            player,
            self._selected_sell_product_id,
            max_w=col_w,
        )

        y = ui.draw_section_header(
            screen,
            fonts,
            x_right,
            row_top,
            "Семена",
            "посадка T · 1–6",
            line_w=col_w,
        )
        y_seeds = self._seed_picker.draw(
            screen,
            fonts,
            x_right,
            y,
            tuple(self._seed_ids),
            self.selected_seed_id,
            player,
            self._plants_meta,
            max_w=col_w,
        )
        y = max(y_products, y_seeds) + 8

        y = ui.draw_section_header(
            screen, fonts, x, y, "Магазин семян", "мука и корм", line_w=inner_w
        )
        money = player["money_bestiki"] if player else 0
        self._shop_buttons = []
        y = ui.draw_shop_grid(
            screen,
            fonts,
            x,
            y,
            self._shop_items,
            money,
            mouse,
            self._shop_buttons,
            max_w=inner_w,
        )

        factory_types = self._factory_types(world)
        if self._recipes and factory_types:
            y = ui.draw_section_header(
                screen, fonts, x, y, "Рецепты", "печь B", line_w=inner_w
            )
            y = self._recipe_picker.draw(
                screen,
                fonts,
                x,
                y,
                self._recipes,
                self._selected_recipe_id,
                player,
                factory_types,
                inner_w,
            )

        if self._animal_items:
            y = ui.draw_section_header(
                screen, fonts, x, y, "Животные", "купить C", line_w=inner_w
            )
            y = self._animal_picker.draw(
                screen, fonts, x, y, self._animal_items, self._selected_animal_id, money
            )

        pid = self.session.player_id
        y = ui.draw_section_header(screen, fonts, x, y, "Заводы", line_w=inner_w)
        y = ui.draw_factories_compact(
            screen,
            fonts,
            x,
            y,
            world.get("factories", []),
            pid,
            self._recipe_by_id,
            line_w=inner_w,
        )

        self._sabotage_click_targets = []
        if self._sabotage_items and self._viewed_opponent_tiles(world):
            y = ui.draw_section_header(
                screen, fonts, x, y, "Саботаж", "клетка соперника", line_w=inner_w
            )
            for sab in self._sabotage_items:
                sab_rect = pygame.Rect(x, y, inner_w, 26)
                can = money >= int(sab.get("price", 0)) and not finished
                label = f"{sab.get('display_name', sab['sabotage_id'])} · {sab['price']} B"
                bg = ui.TILE_ENEMY if can else (210, 205, 198)
                pygame.draw.rect(screen, bg, sab_rect, border_radius=6)
                screen.blit(
                    fonts["tiny"].render(label, True, ui.TEXT if can else ui.TEXT_SOFT),
                    (sab_rect.x + 8, sab_rect.y + 5),
                )
                self._sabotage_click_targets.append((sab["sabotage_id"], sab_rect))
                y += 30
            y += 4

        feed_y = rect.bottom - 16
        visible = events[-3:]
        for ev in reversed(visible):
            msg = ui.humanize_event(ev)
            if msg:
                feed_y -= 16
                screen.blit(
                    fonts["tiny"].render(f"· {msg[:56]}", True, ui.TEXT_SOFT),
                    (x, feed_y),
                )
        if visible:
            feed_y -= 18
            screen.blit(
                fonts["tiny"].render("Лента", True, ui.TEXT_SOFT),
                (x, feed_y),
            )

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
