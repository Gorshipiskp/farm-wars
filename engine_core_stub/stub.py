"""
Python-заглушка для C++ модуля engine_core.

Имеет ТОЧНО ТАКОЙ ЖЕ интерфейс, как настоящий C++ модуль:
    engine_core.simulate_tick(input_dict) -> result_dict

Логика здесь — детерминированная копия C++ simulate_tick.cpp.
Если поведение отличается — это баг.
"""

import copy
import logging

log = logging.getLogger("farm_wars.engine_stub")


# ----- Валидация контракта v1 -----

def _make_error_event(tick_id, error_code, message, field_path=None, player_id=None):
    """Собрать CONTRACT_ERROR событие."""
    return {
        "contract_version": "v1",
        "event_type": "CONTRACT_ERROR",
        "server_tick": tick_id,
        "payload": {
            "error_code": error_code,
            "message": message,
            "field_path": field_path,
            "player_id": player_id,
        },
    }


def _validate_field(d, key, expected_type, path, tick_id, errors):
    """Проверить наличие и тип поля. Добавить ошибку в errors при несоответствии."""
    if key not in d:
        errors.append(_make_error_event(tick_id, "MISSING_FIELD",
                                        f"MISSING_FIELD: {path}.{key}", f"{path}.{key}"))
        return False
    if not isinstance(d[key], expected_type):
        type_name = {str: "string", int: "number", float: "number",
                     dict: "object", list: "array"}.get(expected_type, str(expected_type))
        errors.append(_make_error_event(tick_id, "INVALID_TYPE",
                                        f"INVALID_TYPE: {path}.{key} (expected {type_name})",
                                        f"{path}.{key}"))
        return False
    return True


def validate_tick_input(input_dict):
    """
    Проверить TickInput на соответствие контракту v1.
    Возвращает список CONTRACT_ERROR событий.
    Пустой список = ошибок нет, данные корректны.
    """
    errors = []
    tick_id = input_dict.get("tick_id", 0)

    # --- Верхний уровень TickInput ---
    if not _validate_field(input_dict, "contract_version", str, "tick_input", tick_id, errors):
        pass
    elif input_dict["contract_version"] != "v1":
        errors.append(_make_error_event(tick_id, "UNSUPPORTED_VERSION",
                                        f"Expected v1, got: {input_dict['contract_version']}",
                                        "contract_version"))

    _validate_field(input_dict, "tick_id", (int, float), "tick_input", tick_id, errors)

    has_ws = _validate_field(input_dict, "world_state", dict, "tick_input", tick_id, errors)
    has_actions = _validate_field(input_dict, "actions", list, "tick_input", tick_id, errors)

    if not has_ws:
        return errors  # без world_state дальше нечего валидировать

    # --- world_state ---
    ws = input_dict["world_state"]
    _validate_field(ws, "contract_version", str, "world_state", tick_id, errors)
    _validate_field(ws, "match_id", str, "world_state", tick_id, errors)
    _validate_field(ws, "tick_id", (int, float), "world_state", tick_id, errors)
    _validate_field(ws, "players", list, "world_state", tick_id, errors)

    has_map = _validate_field(ws, "map", dict, "world_state", tick_id, errors)
    if has_map:
        m = ws["map"]
        _validate_field(m, "width", (int, float), "world_state.map", tick_id, errors)
        _validate_field(m, "height", (int, float), "world_state.map", tick_id, errors)
        _validate_field(m, "tiles", list, "world_state.map", tick_id, errors)

    _validate_field(ws, "factories", list, "world_state", tick_id, errors)
    _validate_field(ws, "win_condition", dict, "world_state", tick_id, errors)

    # --- actions ---
    if has_actions:
        for i, action in enumerate(input_dict["actions"]):
            if not isinstance(action, dict):
                errors.append(_make_error_event(
                    tick_id, "INVALID_TYPE",
                    f"actions[{i}] is not an object", f"actions[{i}]"))
                continue
            prefix = f"actions[{i}]"
            _validate_field(action, "contract_version", str, prefix, tick_id, errors)
            _validate_field(action, "player_id", str, prefix, tick_id, errors)
            _validate_field(action, "action_type", str, prefix, tick_id, errors)
            _validate_field(action, "payload", dict, prefix, tick_id, errors)
            _validate_field(action, "client_ts", (int, float), prefix, tick_id, errors)

    return errors


# ----- Основная функция симуляции -----

def simulate_tick(input_dict):
    """Обработать один тик симуляции. Принимает TickInput, возвращает TickResult."""

    tick_id = input_dict.get("tick_id", 0)

    # Шаг 1: валидация
    validation_errors = validate_tick_input(input_dict)
    if validation_errors:
        log.warning(
            "TickInput validation failed tick=%s errors=%s",
            tick_id,
            [e.get("payload", {}).get("message") for e in validation_errors],
        )
        empty_state = {
            "contract_version": "v1",
            "match_id": "error",
            "tick_id": tick_id,
            "players": [],
            "map": {},
            "factories": [],
            "win_condition": {},
        }
        return {
            "contract_version": "v1",
            "tick_id": tick_id,
            "next_world_state": empty_state,
            "events": validation_errors,
        }

    # Шаг 2: извлекаем данные
    world_state = input_dict["world_state"]
    actions = input_dict["actions"]

    # Шаг 3: глубокая копия
    next_world_state = copy.deepcopy(world_state)
    next_world_state["tick_id"] = tick_id

    events = []
    tiles = next_world_state["map"]["tiles"]
    factories = next_world_state["factories"]

    # Шаг 4: обработка действий
    for action in actions:
        action_type = action["action_type"]
        player_id = action["player_id"]
        payload = action["payload"]

        if action_type == "WATER_PLANT":
            tile_id = payload["tile_id"]
            tile = None
            for t in tiles:
                if t["tile_id"] == tile_id:
                    tile = t
                    break

            if tile is None:
                events.append(_make_error_event(tick_id, "MISSING_FIELD", f"Tile not found: {tile_id}"), player_id=player_id)
            elif tile.get("owner_player_id") != player_id:
                events.append(_make_error_event(
                    tick_id, "INVALID_TYPE",
                    f"Tile {tile_id} not owned by {player_id}",
                ))
            else:
                tile["water_level"] = 100
                events.append({
                    "contract_version": "v1",
                    "event_type": "PLANT_WATERED",
                    "server_tick": tick_id,
                    "payload": {"tile_id": tile_id, "player_id": player_id},
                })

        elif action_type == "START_RECIPE":
            factory_id = payload["factory_id"]
            recipe_id = payload["recipe_id"]
            duration_sec = payload["duration_sec"]
            found = False
            for factory in factories:
                if factory["factory_id"] == factory_id:
                    found = True
                    # Проверка владельца
                    if factory.get("owner_player_id") != player_id:
                        events.append({
                            "contract_version": "v1",
                            "event_type": "RECIPE_REJECTED",
                            "server_tick": tick_id,
                            "payload": {
                                "player_id": player_id,
                                "factory_id": factory_id,
                                "recipe_id": recipe_id,
                                "reason": "NOT_OWNER",
                            },
                        })
                        break

                    factory["active_recipe_id"] = recipe_id
                    factory["remaining_time_sec"] = duration_sec
                    if "output_product_id" in payload:
                        factory["output_product_id"] = payload["output_product_id"]

                    events.append({
                        "contract_version": "v1",
                        "event_type": "RECIPE_STARTED",
                        "server_tick": tick_id,
                        "payload": {
                            "factory_id": factory_id,
                            "recipe_id": recipe_id,
                            "player_id": player_id,
                        },
                    })
                    break

            if not found:
                events.append(_make_error_event(tick_id, "MISSING_FIELD",
                    f"Factory not found: {factory_id}", player_id=player_id))

        elif action_type == "PLACE_ON_TILE":
            tile_id = payload["tile_id"]
            plant_id = payload["plant_id"]
            seed_product_id = payload.get("seed_product_id", plant_id)
            initial_health = payload["initial_health"]
            initial_water = payload["initial_water_level"]

            # Найти клетку
            tile = None
            for t in tiles:
                if t["tile_id"] == tile_id:
                    tile = t
                    break

            if tile is None:
                events.append(_make_error_event(tick_id, "MISSING_FIELD", f"Tile not found: {tile_id}"), player_id=player_id)
            elif tile["owner_player_id"] != player_id:
                events.append(_make_error_event(tick_id, "INVALID_TYPE", f"Tile {tile_id} not owned by {player_id}"), player_id=player_id)
            elif tile.get("occupant_type") and tile["occupant_type"] != "EMPTY":
                events.append(_make_error_event(tick_id, "INVALID_TYPE", f"Tile already occupied: {tile_id}"), player_id=player_id)
            elif tile["zone_type"] != "PLANT":
                events.append(_make_error_event(tick_id, "INVALID_TYPE", f"Tile zone is {tile['zone_type']}, expected PLANT"), player_id=player_id)
            else:
                # Проверить инвентарь игрока
                player = None
                for p in next_world_state["players"]:
                    if p["player_id"] == player_id:
                        player = p
                        break

                if player is None:
                    events.append(_make_error_event(tick_id, "MISSING_FIELD", f"Player not found: {player_id}"), player_id=player_id)
                else:
                    inv_found = False
                    for idx, item in enumerate(player["inventory"]):
                        if item["product_id"] != seed_product_id:
                            continue
                        if item["amount"] < 1:
                            events.append(_make_error_event(
                                tick_id, "MISSING_FIELD",
                                f"No {seed_product_id} in inventory for player {player_id}"))
                            inv_found = True
                            break

                        # Списать 1 пакет семян
                        if item["amount"] == 1:
                            del player["inventory"][idx]
                        else:
                            item["amount"] -= 1

                        # Посадить растение (на клетке — тип культуры, не семена)
                        tile["occupant_type"] = "PLANT"
                        crop_id = payload.get("crop_product_id", plant_id)
                        tile["occupant_id"] = crop_id
                        tile["health"] = initial_health
                        if "initial_water_level" in payload:
                            tile["water_level"] = max(0, min(100, int(payload["initial_water_level"])))
                        tile["growth_elapsed_sec"] = 0
                        if "growth_time_sec" in payload:
                            tile["growth_time_sec"] = payload["growth_time_sec"]
                        if "water_decay_per_tick" in payload:
                            tile["water_decay_per_tick"] = payload["water_decay_per_tick"]

                        events.append({
                            "contract_version": "v1",
                            "event_type": "PLANT_PLACED",
                            "server_tick": tick_id,
                            "payload": {
                                "tile_id": tile_id,
                                "plant_id": plant_id,
                                "seed_product_id": seed_product_id,
                                "player_id": player_id,
                            },
                        })
                        inv_found = True
                        break

                    if not inv_found:
                        events.append(_make_error_event(
                            tick_id, "MISSING_FIELD",
                            f"No {seed_product_id} in inventory for player {player_id}"))

        elif action_type in ("BUY_PRODUCT", "BUY_ANIMAL", "APPLY_SABOTAGE", "USE_COUNTERMEASURE"):
            # Server-only — ignore if leaked into engine queue
            pass

        elif action_type == "FEED_ANIMAL":
            tile_id = payload.get("tile_id")
            tile = next((t for t in tiles if t.get("tile_id") == tile_id), None)
            if tile is None:
                events.append({
                    "contract_version": "v1",
                    "event_type": "FEED_FAILED",
                    "server_tick": tick_id,
                    "payload": {
                        "player_id": player_id,
                        "tile_id": tile_id,
                        "reason": "UNKNOWN_TILE",
                    },
                })
            elif tile.get("owner_player_id") != player_id:
                events.append({
                    "contract_version": "v1",
                    "event_type": "FEED_FAILED",
                    "server_tick": tick_id,
                    "payload": {
                        "player_id": player_id,
                        "tile_id": tile_id,
                        "reason": "NOT_OWNER",
                    },
                })
            elif tile.get("occupant_type") != "ANIMAL":
                events.append({
                    "contract_version": "v1",
                    "event_type": "FEED_FAILED",
                    "server_tick": tick_id,
                    "payload": {
                        "player_id": player_id,
                        "tile_id": tile_id,
                        "reason": "NO_ANIMAL",
                    },
                })
            else:
                if "production_interval_sec" in payload:
                    tile["production_interval_sec"] = payload["production_interval_sec"]
                if "product_id" in payload:
                    tile["product_id"] = payload["product_id"]
                tile["hunger_ticks"] = 0
                ev_feed = {
                    "player_id": player_id,
                    "tile_id": tile_id,
                }
                animal_id = tile.get("occupant_id")
                if animal_id:
                    ev_feed["animal_id"] = animal_id
                events.append({
                    "contract_version": "v1",
                    "event_type": "ANIMAL_FED",
                    "server_tick": tick_id,
                    "payload": ev_feed,
                })

        elif action_type == "APPLY_EVENT":
            event_type = payload["event_type"]
            affected = 0

            if event_type == "DROUGHT":
                # Засуха: скорость высыхания +50%
                for t in tiles:
                    if t.get("occupant_type") != "PLANT":
                        continue
                    decay = t.get("water_decay_per_tick") or 2
                    decay = max(1, int(decay * 1.5))
                    t["water_decay_per_tick"] = decay
                    affected += 1

            elif event_type in ("RAIN", "FLOOD"):
                # Дождь: влажность растет (decay отрицательный)
                for t in tiles:
                    w = t.get("water_level")
                    if w is None:
                        continue
                    decay = t.get("water_decay_per_tick") or 1
                    if decay < 0:
                        decay = 1  # уже идет дождь
                    increase = max(1, int(decay * 0.2))
                    t["water_decay_per_tick"] = -increase
                    affected += 1

            elif event_type == "EARTHQUAKE":
                # Землетрясение: заводы +50% времени
                for f in next_world_state["factories"]:
                    if not f.get("active_recipe_id"):
                        continue
                    remaining = f.get("remaining_time_sec", 0)
                    if remaining <= 0:
                        continue
                    f["remaining_time_sec"] = int(remaining * 1.5)
                    affected += 1

            elif event_type == "EPIDEMIC":
                # Эпидемия: замедление надоя (интервал ×1.5)
                for t in tiles:
                    if t.get("occupant_type") != "ANIMAL":
                        continue
                    interval = t.get("production_interval_sec") or 12
                    t["production_interval_sec"] = int(interval * 1.5)
                    affected += 1

            else:
                events.append(_make_error_event(tick_id, "INVALID_TYPE", f"Unknown event_type: {event_type}"), player_id=player_id)

            if affected > 0 or event_type in (
                "DROUGHT", "RAIN", "FLOOD", "EARTHQUAKE", "EPIDEMIC",
            ):
                events.append({
                    "contract_version": "v1",
                    "event_type": "EVENT_TRIGGERED",
                    "server_tick": tick_id,
                    "payload": {
                        "event_type": event_type,
                        "severity": 1.0,
                        "affected_tiles": affected,
                    },
                })

        elif action_type == "HARVEST_PLANT":
            tile_id = payload["tile_id"]

            # Найти клетку
            tile = None
            for t in tiles:
                if t["tile_id"] == tile_id:
                    tile = t
                    break

            if tile is None:
                events.append({
                    "contract_version": "v1",
                    "event_type": "HARVEST_FAILED",
                    "server_tick": tick_id,
                    "payload": {"player_id": player_id, "tile_id": tile_id, "reason": "UNKNOWN_TILE"},
                })
            elif tile["owner_player_id"] != player_id:
                events.append({
                    "contract_version": "v1",
                    "event_type": "HARVEST_FAILED",
                    "server_tick": tick_id,
                    "payload": {"player_id": player_id, "tile_id": tile_id, "reason": "NOT_OWNER"},
                })
            elif tile.get("occupant_type") != "PLANT":
                events.append({
                    "contract_version": "v1",
                    "event_type": "HARVEST_FAILED",
                    "server_tick": tick_id,
                    "payload": {"player_id": player_id, "tile_id": tile_id, "reason": "NO_PLANT"},
                })
            elif ("growth_time_sec" in tile and tile["growth_time_sec"] is not None and
                  "growth_elapsed_sec" in tile and tile["growth_elapsed_sec"] is not None and
                  tile["growth_elapsed_sec"] < tile["growth_time_sec"]):
                events.append({
                    "contract_version": "v1",
                    "event_type": "HARVEST_FAILED",
                    "server_tick": tick_id,
                    "payload": {"player_id": player_id, "tile_id": tile_id, "reason": "NOT_RIPE"},
                })
            elif tile.get("water_level") is not None and tile["water_level"] < 50:
                events.append({
                    "contract_version": "v1",
                    "event_type": "HARVEST_FAILED",
                    "server_tick": tick_id,
                    "payload": {"player_id": player_id, "tile_id": tile_id, "reason": "NOT_READY"},
                })
            else:
                # Успех
                product_id = tile.get("occupant_id", "")
                HARVEST_YIELD = 2

                for p in next_world_state["players"]:
                    if p["player_id"] != player_id:
                        continue
                    found = False
                    for item in p["inventory"]:
                        if item["product_id"] == product_id:
                            item["amount"] += HARVEST_YIELD
                            found = True
                            break
                    if not found:
                        p["inventory"].append({"product_id": product_id, "amount": HARVEST_YIELD})
                    break

                tile["occupant_type"] = "EMPTY"
                tile["occupant_id"] = None
                tile["health"] = None
                tile["growth_elapsed_sec"] = None
                tile["growth_time_sec"] = None
                tile["water_decay_per_tick"] = None

                events.append({
                    "contract_version": "v1",
                    "event_type": "PLANT_HARVESTED",
                    "server_tick": tick_id,
                    "payload": {
                        "player_id": player_id,
                        "tile_id": tile_id,
                        "product_id": product_id,
                        "amount": HARVEST_YIELD,
                    },
                })

        else:
            log.warning(
                "Unknown action_type=%s player=%s",
                action_type, player_id,
            )
            events.append(_make_error_event(tick_id, "INVALID_TYPE", f"Unknown action_type: {action_type}"))

    # Шаг 4.5: пассивная фаза — испарение со всех грядок, рост/смерть растений
    HEALTH_DECAY_PER_TICK = 10
    DEFAULT_EVAPORATION = 0

    for tile in next_world_state["map"]["tiles"]:
        # Испарение — для всех грядок с водой
        water = tile.get("water_level")
        if water is not None and water > 0:
            decay = tile.get("water_decay_per_tick") or DEFAULT_EVAPORATION
            water = max(0, min(100, water - decay))
            tile["water_level"] = water

        # Дальше — только растения
        if tile.get("occupant_type") != "PLANT":
            continue

        water = tile.get("water_level") or 0

        # Рост (если есть вода)
        if water > 0:
            tile["growth_elapsed_sec"] = tile.get("growth_elapsed_sec", 0) + 1
            continue

        # Без воды — потеря здоровья
        health = tile.get("health") or 100
        health -= HEALTH_DECAY_PER_TICK

        if health <= 0:
            dead_plant = tile.get("occupant_id", "")
            dead_tile = tile.get("tile_id", "")
            owner = tile.get("owner_player_id", "")
            tile["occupant_type"] = "EMPTY"
            tile["occupant_id"] = None
            tile["health"] = None
            tile["growth_elapsed_sec"] = None
            tile["growth_time_sec"] = None
            tile["water_decay_per_tick"] = None
            events.append({
                "contract_version": "v1",
                "event_type": "PLANT_DIED",
                "server_tick": tick_id,
                "payload": {
                    "tile_id": dead_tile,
                    "plant_id": dead_plant,
                    "player_id": owner,
                    "reason": "DEHYDRATED",
                },
            })
        else:
            tile["health"] = health

    # Шаг 4.55: пассивная фаза животных — голод и надой
    from shared.game_pacing import ANIMAL_HUNGER_LIMIT_TICKS

    ANIMAL_HUNGER_LIMIT = ANIMAL_HUNGER_LIMIT_TICKS

    for tile in next_world_state["map"]["tiles"]:
        if tile.get("occupant_type") != "ANIMAL" or not tile.get("occupant_id"):
            continue

        hunger = tile.get("hunger_ticks", 0) + 1
        tile["hunger_ticks"] = hunger
        if hunger > ANIMAL_HUNGER_LIMIT:
            continue

        interval = tile.get("production_interval_sec") or 12
        elapsed = tile.get("production_elapsed_sec", 0) + 1
        tile["production_elapsed_sec"] = elapsed
        if elapsed < interval:
            continue

        tile["production_elapsed_sec"] = 0
        product_id = tile.get("product_id") or "milk"
        owner_id = tile.get("owner_player_id", "")

        for p in next_world_state["players"]:
            if p["player_id"] != owner_id:
                continue
            found = False
            for item in p["inventory"]:
                if item["product_id"] == product_id:
                    item["amount"] += 1
                    found = True
                    break
            if not found:
                p["inventory"].append({"product_id": product_id, "amount": 1})
            break

        events.append({
            "contract_version": "v1",
            "event_type": "ANIMAL_PRODUCED",
            "server_tick": tick_id,
            "payload": {
                "player_id": owner_id,
                "tile_id": tile.get("tile_id"),
                "product_id": product_id,
                "amount": 1,
            },
        })

    # Шаг 4.6: пассивная фаза заводов — таймер рецепта
    for factory in next_world_state["factories"]:
        if not factory.get("active_recipe_id"):
            continue
        remaining = factory.get("remaining_time_sec", 0)
        if remaining <= 0:
            continue

        remaining -= 1
        factory["remaining_time_sec"] = remaining

        if remaining > 0:
            continue

        # Рецепт завершен
        recipe_id = factory["active_recipe_id"]
        owner_id = factory["owner_player_id"]
        factory_id = factory["factory_id"]
        product_id = factory.get("output_product_id") or recipe_id

        for p in next_world_state["players"]:
            if p["player_id"] != owner_id:
                continue
            found = False
            for item in p["inventory"]:
                if item["product_id"] == product_id:
                    item["amount"] += 1
                    found = True
                    break
            if not found:
                p["inventory"].append({"product_id": product_id, "amount": 1})
            break

        factory["active_recipe_id"] = None
        factory["output_product_id"] = None

        events.append({
            "contract_version": "v1",
            "event_type": "RECIPE_FINISHED",
            "server_tick": tick_id,
            "payload": {
                "factory_id": factory_id,
                "recipe_id": recipe_id,
                "product_id": product_id,
                "player_id": owner_id,
            },
        })

        # Авто-запуск из очереди
        queue = factory.get("queue", [])
        if queue:
            next_job = queue.pop(0)
            next_recipe = next_job["recipe_id"]
            duration = next_job.get("duration_sec", 30)
            factory["active_recipe_id"] = next_recipe
            factory["remaining_time_sec"] = duration
            events.append({
                "contract_version": "v1",
                "event_type": "RECIPE_STARTED",
                "server_tick": tick_id,
                "payload": {
                    "factory_id": factory_id,
                    "recipe_id": next_recipe,
                    "player_id": owner_id,
                },
            })

    # Шаг 5: результат
    return {
        "contract_version": "v1",
        "tick_id": tick_id,
        "next_world_state": next_world_state,
        "events": events,
    }
