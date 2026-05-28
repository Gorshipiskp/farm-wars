"""
Контракты данных v1 для Farm Wars.

Эти классы описывают структуры, которыми обмениваются:
- клиент <-> сервер (PlayerAction, ServerEvent, StateSyncEvent),
- сервер <-> C++ движок (TickInput, TickResult).

Все классы умеют превращаться в dict (для отправки) и создаваться из dict (для получения).
"""


class PlayerAction:
    """Действие игрока, которое клиент отправляет на сервер."""

    def __init__(self, player_id, action_type, payload, client_ts):
        self.contract_version = "v1"
        self.player_id = player_id  # кто сделал
        self.action_type = action_type  # например "WATER_PLANT"
        self.payload = payload  # доп. данные действия (dict)
        self.client_ts = client_ts  # unix время в миллисекундах

    def to_dict(self):
        return {
            "contract_version": self.contract_version,
            "player_id": self.player_id,
            "action_type": self.action_type,
            "payload": self.payload,
            "client_ts": self.client_ts,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            player_id=d["player_id"],
            action_type=d["action_type"],
            payload=d["payload"],
            client_ts=d["client_ts"],
        )


class ServerEvent:
    """Событие, которое сервер рассылает клиентам после обработки тика."""

    def __init__(self, event_type, payload, server_tick):
        self.contract_version = "v1"
        self.event_type = event_type  # например "PLANT_WATERED"
        self.payload = payload  # dict с деталями
        self.server_tick = server_tick  # на каком тике произошло

    def to_dict(self):
        return {
            "contract_version": self.contract_version,
            "event_type": self.event_type,
            "payload": self.payload,
            "server_tick": self.server_tick,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            event_type=d["event_type"],
            payload=d["payload"],
            server_tick=d["server_tick"],
        )


class InventoryItem:
    """Одна позиция в инвентаре игрока."""

    def __init__(self, product_id, amount):
        self.product_id = product_id
        self.amount = amount

    def to_dict(self):
        return {"product_id": self.product_id, "amount": self.amount}

    @classmethod
    def from_dict(cls, d):
        return cls(product_id=d["product_id"], amount=d["amount"])


class TileState:
    """Одна клетка игрового поля."""

    def __init__(self, tile_id, zone_type, owner_player_id,
                 occupant_type=None, occupant_id=None,
                 health=None, water_level=None, flags=None):
        self.tile_id = tile_id
        self.zone_type = zone_type  # "PLANT" или "ANIMAL"
        self.owner_player_id = owner_player_id
        self.occupant_type = occupant_type  # "PLANT", "ANIMAL" или None
        self.occupant_id = occupant_id
        self.health = health
        self.water_level = water_level
        self.flags = flags or []  # например ["MINED"]

    def to_dict(self):
        result = {
            "tile_id": self.tile_id,
            "zone_type": self.zone_type,
            "owner_player_id": self.owner_player_id,
        }
        if self.occupant_type is not None:
            result["occupant_type"] = self.occupant_type
        if self.occupant_id is not None:
            result["occupant_id"] = self.occupant_id
        if self.health is not None:
            result["health"] = self.health
        if self.water_level is not None:
            result["water_level"] = self.water_level
        if self.flags:
            result["flags"] = self.flags
        return result

    @classmethod
    def from_dict(cls, d):
        return cls(
            tile_id=d["tile_id"],
            zone_type=d["zone_type"],
            owner_player_id=d["owner_player_id"],
            occupant_type=d.get("occupant_type"),
            occupant_id=d.get("occupant_id"),
            health=d.get("health"),
            water_level=d.get("water_level"),
            flags=d.get("flags", []),
        )


class MapState:
    """Игровое поле: размер и список клеток."""

    def __init__(self, width, height, tiles):
        self.width = width
        self.height = height
        self.tiles = tiles  # список TileState

    def to_dict(self):
        return {
            "width": self.width,
            "height": self.height,
            "tiles": [t.to_dict() for t in self.tiles],
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            width=d["width"],
            height=d["height"],
            tiles=[TileState.from_dict(t) for t in d["tiles"]],
        )


class QueueItem:
    """Элемент очереди завода — рецепт, ожидающий запуска."""

    def __init__(self, recipe_id, requested_amount):
        self.recipe_id = recipe_id
        self.requested_amount = requested_amount

    def to_dict(self):
        return {"recipe_id": self.recipe_id, "requested_amount": self.requested_amount}

    @classmethod
    def from_dict(cls, d):
        return cls(recipe_id=d["recipe_id"], requested_amount=d["requested_amount"])


class FactoryState:
    """Состояние одного завода (переработчика)."""

    def __init__(self, factory_id, factory_type, owner_player_id, level,
                 active_recipe_id, remaining_time_sec, queue):
        self.factory_id = factory_id
        self.factory_type = factory_type  # например "BAKERY"
        self.owner_player_id = owner_player_id
        self.level = level  # >= 1
        self.active_recipe_id = active_recipe_id  # None если простаивает
        self.remaining_time_sec = remaining_time_sec  # >= 0
        self.queue = queue  # список QueueItem

    def to_dict(self):
        return {
            "factory_id": self.factory_id,
            "factory_type": self.factory_type,
            "owner_player_id": self.owner_player_id,
            "level": self.level,
            "active_recipe_id": self.active_recipe_id,
            "remaining_time_sec": self.remaining_time_sec,
            "queue": [q.to_dict() for q in self.queue],
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            factory_id=d["factory_id"],
            factory_type=d["factory_type"],
            owner_player_id=d["owner_player_id"],
            level=d["level"],
            active_recipe_id=d["active_recipe_id"],
            remaining_time_sec=d["remaining_time_sec"],
            queue=[QueueItem.from_dict(q) for q in d["queue"]],
        )


class PlayerState:
    """Состояние одного игрока."""

    def __init__(self, player_id, display_name, money_bestiki, inventory, status_effects=None):
        self.player_id = player_id
        self.display_name = display_name
        self.money_bestiki = money_bestiki  # количество валюты
        self.inventory = inventory  # список InventoryItem
        self.status_effects = status_effects or []

    def to_dict(self):
        result = {
            "player_id": self.player_id,
            "display_name": self.display_name,
            "money_bestiki": self.money_bestiki,
            "inventory": [i.to_dict() for i in self.inventory],
        }
        if self.status_effects:
            result["status_effects"] = self.status_effects
        return result

    @classmethod
    def from_dict(cls, d):
        return cls(
            player_id=d["player_id"],
            display_name=d["display_name"],
            money_bestiki=d["money_bestiki"],
            inventory=[InventoryItem.from_dict(i) for i in d["inventory"]],
            status_effects=d.get("status_effects", []),
        )


class WinConditionState:
    """Текущее состояние победного условия матча."""

    def __init__(self, condition_type, target_product_id, winner_player_id):
        self.condition_type = condition_type  # "FIRST_PRODUCT"
        self.target_product_id = target_product_id  # какой продукт нужен
        self.winner_player_id = winner_player_id  # None пока нет победителя

    def to_dict(self):
        return {
            "condition_type": self.condition_type,
            "target_product_id": self.target_product_id,
            "winner_player_id": self.winner_player_id,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            condition_type=d["condition_type"],
            target_product_id=d["target_product_id"],
            winner_player_id=d["winner_player_id"],
        )


class WorldState:
    """Полное состояние игрового мира на конкретный тик."""

    def __init__(self, match_id, tick_id, players, game_map, factories, win_condition):
        self.contract_version = "v1"
        self.match_id = match_id
        self.tick_id = tick_id
        self.players = players  # список PlayerState
        self.map = game_map  # MapState
        self.factories = factories  # список FactoryState
        self.win_condition = win_condition  # WinConditionState

    def to_dict(self):
        return {
            "contract_version": self.contract_version,
            "match_id": self.match_id,
            "tick_id": self.tick_id,
            "players": [p.to_dict() for p in self.players],
            "map": self.map.to_dict(),
            "factories": [f.to_dict() for f in self.factories],
            "win_condition": self.win_condition.to_dict(),
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            match_id=d["match_id"],
            tick_id=d["tick_id"],
            players=[PlayerState.from_dict(p) for p in d["players"]],
            game_map=MapState.from_dict(d["map"]),
            factories=[FactoryState.from_dict(f) for f in d["factories"]],
            win_condition=WinConditionState.from_dict(d["win_condition"]),
        )


class TickInput:
    """Что Python-сервер передает в C++ движок на каждом тике."""

    def __init__(self, tick_id, world_state, actions):
        self.contract_version = "v1"
        self.tick_id = tick_id
        self.world_state = world_state  # WorldState
        self.actions = actions  # список PlayerAction

    def to_dict(self):
        return {
            "contract_version": self.contract_version,
            "tick_id": self.tick_id,
            "world_state": self.world_state.to_dict(),
            "actions": [a.to_dict() for a in self.actions],
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            tick_id=d["tick_id"],
            world_state=WorldState.from_dict(d["world_state"]),
            actions=[PlayerAction.from_dict(a) for a in d["actions"]],
        )


class TickResult:
    """Что C++ движок возвращает Python-серверу после обработки тика."""

    def __init__(self, tick_id, next_world_state, events):
        self.contract_version = "v1"
        self.tick_id = tick_id
        self.next_world_state = next_world_state  # WorldState
        self.events = events  # список ServerEvent

    def to_dict(self):
        return {
            "contract_version": self.contract_version,
            "tick_id": self.tick_id,
            "next_world_state": self.next_world_state.to_dict(),
            "events": [e.to_dict() for e in self.events],
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            tick_id=d["tick_id"],
            next_world_state=WorldState.from_dict(d["next_world_state"]),
            events=[ServerEvent.from_dict(e) for e in d["events"]],
        )


# --- Клиент-серверные обертки (из GAME_CONTRACTS_V1, секция 6) ---

class CreateMatchResponse:
    """Ответ сервера на создание матча."""

    def __init__(self, match_id, join_code):
        self.contract_version = "v1"
        self.match_id = match_id
        self.join_code = join_code

    def to_dict(self):
        return {
            "contract_version": self.contract_version,
            "match_id": self.match_id,
            "join_code": self.join_code,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(match_id=d["match_id"], join_code=d["join_code"])


class JoinMatchRequest:
    """Запрос клиента на вход в матч."""

    def __init__(self, join_code, player_name):
        self.contract_version = "v1"
        self.join_code = join_code
        self.player_name = player_name

    def to_dict(self):
        return {
            "contract_version": self.contract_version,
            "join_code": self.join_code,
            "player_name": self.player_name,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(join_code=d["join_code"], player_name=d["player_name"])


class JoinMatchResponse:
    """Ответ сервера на вход в матч."""

    def __init__(self, match_id, player_id):
        self.contract_version = "v1"
        self.match_id = match_id
        self.player_id = player_id

    def to_dict(self):
        return {
            "contract_version": self.contract_version,
            "match_id": self.match_id,
            "player_id": self.player_id,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(match_id=d["match_id"], player_id=d["player_id"])


class ClientActionEnvelope:
    """Конверт для отправки PlayerAction от клиента к серверу."""

    def __init__(self, match_id, player_id, action):
        self.contract_version = "v1"
        self.match_id = match_id
        self.player_id = player_id
        self.action = action  # PlayerAction

    def to_dict(self):
        return {
            "contract_version": self.contract_version,
            "match_id": self.match_id,
            "player_id": self.player_id,
            "action": self.action.to_dict(),
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            match_id=d["match_id"],
            player_id=d["player_id"],
            action=PlayerAction.from_dict(d["action"]),
        )


class StateSyncEvent:
    """Сервер рассылает клиентам новое состояние мира после тика."""

    def __init__(self, match_id, tick_id, world_state, events):
        self.contract_version = "v1"
        self.match_id = match_id
        self.tick_id = tick_id
        self.world_state = world_state  # WorldState
        self.events = events  # список ServerEvent

    def to_dict(self):
        return {
            "contract_version": self.contract_version,
            "match_id": self.match_id,
            "tick_id": self.tick_id,
            "world_state": self.world_state.to_dict(),
            "events": [e.to_dict() for e in self.events],
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            match_id=d["match_id"],
            tick_id=d["tick_id"],
            world_state=WorldState.from_dict(d["world_state"]),
            events=[ServerEvent.from_dict(e) for e in d["events"]],
        )
