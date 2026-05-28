"""
Farm Wars pygame client — lobby + match UI.

Client zone only: uses server HTTP API, does not change server/engine/contracts.

Run (server must be up):
    py tools/init_db.py --seed
    py -m server
    py -m client
    py -m client --host 192.168.0.5 --port 8765

Requires: pip install -r client/requirements.txt
"""

import argparse
import logging
import os

import pygame

from client.net import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    ServerClient,
    ServerError,
    parse_server_address,
)
from client.session import ClientSession
from client.sync_poller import SyncPoller

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("farm_wars.client")

# --- Layout ---
WIDTH, HEIGHT = 960, 700
TILE_SIZE = 72
GRID_X, GRID_Y = 24, 120
PANEL_X = 420

# --- Colors ---
BG = (28, 42, 28)
PANEL = (40, 55, 40)
TILE_PLANT = (76, 120, 68)
TILE_EMPTY = (55, 75, 50)
TILE_SEL = (200, 180, 60)
TEXT = (240, 240, 230)
ERROR = (220, 80, 80)
OK = (100, 200, 120)
BTN = (70, 100, 70)
BTN_HOVER = (90, 130, 90)

STATE_LOBBY = "lobby"
STATE_MATCH = "match"


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
            elif event.key == pygame.K_RETURN:
                pass
            elif len(self.text) < 24 and event.unicode.isprintable():
                self.text += event.unicode

    def draw(self, screen, font):
        color = (55, 70, 55) if self.active else (45, 58, 45)
        pygame.draw.rect(screen, color, self.rect, border_radius=4)
        pygame.draw.rect(screen, (90, 110, 90), self.rect, 1, border_radius=4)
        label = self.text if self.text else self.placeholder
        shade = (140, 140, 130) if not self.text else TEXT
        screen.blit(font.render(label, True, shade), (self.rect.x + 8, self.rect.y + 8))


class Button:
    def __init__(self, rect, label):
        self.rect = pygame.Rect(rect)
        self.label = label

    def draw(self, screen, font, mouse_pos):
        hover = self.rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, BTN_HOVER if hover else BTN, self.rect, border_radius=6)
        text = font.render(self.label, True, TEXT)
        screen.blit(
            text,
            text.get_rect(center=self.rect.center),
        )

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)


class FarmWarsApp:
    def __init__(self, server_host: str = DEFAULT_HOST, server_port: int = DEFAULT_PORT):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Farm Wars")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 18)
        self.font_sm = pygame.font.SysFont("consolas", 14)
        self.font_lg = pygame.font.SysFont("consolas", 28)

        self.session = ClientSession()
        self.state = STATE_LOBBY
        self.status_msg = "Enter server IP and create or join"
        self.selected_tile_id: str | None = None

        self.field_server = TextField((40, 100, 220, 36), "Server IP")
        self.field_server.text = server_host
        self.field_port = TextField((270, 100, 90, 36), "8765")
        self.field_port.text = str(server_port)
        self.field_name = TextField((40, 180, 320, 36), "Player name")
        self.field_code = TextField((40, 260, 320, 36), "Join code")
        self.btn_connect = Button((40, 320, 150, 40), "Connect")
        self.btn_create = Button((210, 320, 150, 40), "Create")
        self.btn_join = Button((40, 380, 150, 40), "Join")
        self.btn_start = Button((210, 380, 150, 40), "Start")

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
            engine = health.get("engine", "?")
            self.status_msg = f"Connected to {base} ({engine})"
            self.session.clear_error()
            return True
        except ServerError as exc:
            self.status_msg = f"Cannot reach server: {exc.message}"
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

            self.screen.fill(BG)
            if self.state == STATE_LOBBY:
                self._draw_lobby(mouse)
            else:
                self._draw_match(mouse)

            pygame.display.flip()
            self.clock.tick(30)

        self.poller.stop()
        pygame.quit()

    # --- Lobby ---

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
        name = self.field_name.text.strip() or "Host"
        try:
            res = self.net.create_match(name)
            self.session.player_name = name
            self.session.match_id = res["match_id"]
            self.session.player_id = "p1"
            self.session.join_code = res["join_code"]
            self.session.is_host = True
            self.field_code.text = res["join_code"]
            self.status_msg = f"Created. Share code: {res['join_code']}"
            self.session.clear_error()
        except ServerError as exc:
            self.status_msg = f"{exc.error_code}: {exc.message}"

    def _do_join(self):
        if not self._check_server():
            return
        name = self.field_name.text.strip() or "Guest"
        code = self.field_code.text.strip().upper()
        if not code:
            self.status_msg = "Enter join code"
            return
        try:
            res = self.net.join_match(code, name)
            self.session.player_name = name
            self.session.match_id = res["match_id"]
            self.session.player_id = res["player_id"]
            self.session.join_code = code
            self.session.is_host = False
            self.status_msg = f"Joined as {res['player_id']}"
            self.session.clear_error()
        except ServerError as exc:
            self.status_msg = f"{exc.error_code}: {exc.message}"

    def _do_start(self):
        if not self.session.match_id:
            self.status_msg = "Create or join first"
            return
        if not self._check_server():
            return
        try:
            self.net.start_match(self.session.match_id)
            self.state = STATE_MATCH
            self.poller.start()
            self.status_msg = "Match running"
            self.session.clear_error()
        except ServerError as exc:
            self.status_msg = f"{exc.error_code}: {exc.message}"

    def _draw_lobby(self, mouse):
        self.screen.blit(self.font_lg.render("Farm Wars — Lobby", True, TEXT), (40, 32))
        self.screen.blit(self.font_sm.render("Server IP", True, (180, 180, 170)), (40, 82))
        self.screen.blit(self.font_sm.render("Port", True, (180, 180, 170)), (270, 82))
        self.field_server.draw(self.screen, self.font)
        self.field_port.draw(self.screen, self.font)
        self.field_name.draw(self.screen, self.font)
        self.field_code.draw(self.screen, self.font)
        self.btn_connect.draw(self.screen, self.font, mouse)
        self.btn_create.draw(self.screen, self.font, mouse)
        self.btn_join.draw(self.screen, self.font, mouse)
        if self.session.is_host and self.session.match_id:
            self.btn_start.draw(self.screen, self.font, mouse)
        url = parse_server_address(self.field_server.text, self.field_port.text)
        self.screen.blit(self.font_sm.render(f"URL: {url}", True, (150, 160, 150)), (40, 455))
        self._draw_status()

    # --- Match ---

    def _match_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                self._send_water()
            elif event.key == pygame.K_t:
                self._send_place()
            elif event.key == pygame.K_b:
                self._send_recipe()
            elif event.key == pygame.K_ESCAPE:
                self.state = STATE_LOBBY
                self.poller.stop()
                self.status_msg = "Left match (lobby)"

        if event.type == pygame.MOUSEBUTTONDOWN:
            self._pick_tile(event.pos)

    def _pick_tile(self, pos):
        world, *_ = self.session.snapshot()
        if not world:
            return
        for tile in self._my_tiles(world):
            rect = self._tile_rect(tile)
            if rect.collidepoint(pos):
                self.selected_tile_id = tile["tile_id"]
                return

    def _my_tiles(self, world):
        pid = self.session.player_id
        return [t for t in world.get("map", {}).get("tiles", []) if t.get("owner_player_id") == pid]

    def _tile_rect(self, tile):
        world = self.session.world_state
        if not world:
            return pygame.Rect(0, 0, 0, 0)
        my_tiles = self._my_tiles(world)
        try:
            index = next(i for i, t in enumerate(my_tiles) if t["tile_id"] == tile["tile_id"])
        except StopIteration:
            index = 0
        col = index % 3
        row = index // 3
        return pygame.Rect(GRID_X + col * (TILE_SIZE + 8), GRID_Y + row * (TILE_SIZE + 8), TILE_SIZE, TILE_SIZE)

    def _send_action(self, action_type: str, payload: dict):
        if self.session.match_finished:
            self.status_msg = "Match finished"
            return
        try:
            action = self.net.make_action(self.session.player_id, action_type, payload)
            self.net.submit_action(self.session.match_id, self.session.player_id, action)
            self.session.clear_error()
            self.status_msg = f"Sent {action_type}"
        except ServerError as exc:
            self.session.set_error(f"{exc.error_code}: {exc.message}")
            self.status_msg = self.session.last_error

    def _send_water(self):
        if not self.selected_tile_id:
            self.status_msg = "Select a tile first"
            return
        self._send_action("WATER_PLANT", {"tile_id": self.selected_tile_id})

    def _send_place(self):
        if not self.selected_tile_id:
            self.status_msg = "Select a tile first"
            return
        self._send_action("PLACE_ON_TILE", {
            "tile_id": self.selected_tile_id,
            "plant_id": "wheat",
        })

    def _send_recipe(self):
        world, *_ = self.session.snapshot()
        if not world:
            return
        pid = self.session.player_id
        factory = None
        for f in world.get("factories", []):
            if f.get("owner_player_id") == pid:
                factory = f
                break
        if not factory:
            self.status_msg = "No factory"
            return
        recipe = world.get("win_condition", {}).get("target_product_id", "bread")
        self._send_action("START_RECIPE", {
            "factory_id": factory["factory_id"],
            "recipe_id": recipe,
            "duration_sec": 30,
        })

    def _draw_match(self, mouse):
        world, tick, events, err, finished = self.session.snapshot()
        self.screen.blit(self.font_lg.render("Match", True, TEXT), (24, 16))

        if world:
            self._draw_tiles(world)
            self._draw_hud(world, tick, events)
        else:
            self.screen.blit(self.font.render("Waiting for sync...", True, TEXT), (GRID_X, GRID_Y))

        hint = "Click tile | W=water | T=plant | B=bake | Esc=lobby"
        self.screen.blit(self.font_sm.render(hint, True, (180, 180, 170)), (24, HEIGHT - 56))

        if err:
            self.screen.blit(self.font.render(err, True, ERROR), (24, HEIGHT - 28))
        elif finished:
            win = world.get("win_condition", {}).get("winner_player_id") if world else "?"
            self.screen.blit(
                self.font.render(f"Match finished! Winner: {win}", True, OK),
                (24, HEIGHT - 28),
            )
        else:
            self._draw_status()

    def _draw_tiles(self, world):
        for tile in self._my_tiles(world):
            rect = self._tile_rect(tile)
            empty = tile.get("occupant_type") == "EMPTY"
            color = TILE_EMPTY if empty else TILE_PLANT
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            if tile["tile_id"] == self.selected_tile_id:
                pygame.draw.rect(self.screen, TILE_SEL, rect, 3, border_radius=6)
            occ = tile.get("occupant_id") or "empty"
            water = tile.get("water_level")
            label = f"{tile['tile_id'][-2:]}"
            self.screen.blit(self.font_sm.render(label, True, TEXT), (rect.x + 4, rect.y + 4))
            if water is not None:
                self.screen.blit(self.font_sm.render(f"H2O:{water}", True, TEXT), (rect.x + 4, rect.y + 24))

    def _draw_hud(self, world, tick, events):
        pygame.draw.rect(self.screen, PANEL, (PANEL_X, 80, WIDTH - PANEL_X - 16, HEIGHT - 100), border_radius=8)
        x = PANEL_X + 16
        y = 96
        pid = self.session.player_id

        player = next((p for p in world.get("players", []) if p["player_id"] == pid), None)
        money = player["money_bestiki"] if player else 0
        win = world.get("win_condition", {})

        lines = [
            f"Player: {pid} ({self.session.player_name})",
            f"Tick: {tick}",
            f"Money: {money} Bestiki",
            f"Goal: {win.get('target_product_id', '?')}",
            "",
            "Factories:",
        ]
        for f in world.get("factories", []):
            if f.get("owner_player_id") != pid:
                continue
            active = f.get("active_recipe_id") or "idle"
            rem = f.get("remaining_time_sec", 0)
            lines.append(f"  {f['factory_id']}: {active} ({rem}s)")

        if events:
            lines.append("")
            lines.append("Last events:")
            for ev in events[-4:]:
                lines.append(f"  {ev.get('event_type')}")

        for line in lines:
            self.screen.blit(self.font_sm.render(line, True, TEXT), (x, y))
            y += 22

    def _draw_status(self):
        y = 430 if self.state == STATE_LOBBY else HEIGHT - 28
        self.screen.blit(self.font.render(self.status_msg, True, TEXT), (40, y))


def main():
    parser = argparse.ArgumentParser(description="Farm Wars client")
    parser.add_argument(
        "--host",
        default=os.environ.get("FARM_WARS_SERVER_HOST", DEFAULT_HOST),
        help="Server IP or hostname (default 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("FARM_WARS_SERVER_PORT", str(DEFAULT_PORT))),
        help="Server port (default 8765)",
    )
    args = parser.parse_args()

    try:
        FarmWarsApp(server_host=args.host, server_port=args.port).run()
    except pygame.error as exc:
        log.error("Pygame failed (display available?): %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
