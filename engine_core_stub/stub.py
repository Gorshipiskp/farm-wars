"""
Python-заглушка для C++ модуля engine_core.

Имеет ТОЧНО ТАКОЙ ЖЕ интерфейс, как настоящий C++ модуль:
    engine_core.simulate_tick(input_dict) -> result_dict

Логика здесь — детерминированная копия C++ simulate_tick.cpp.
Если поведение отличается — это баг.
"""

import copy


# ----- Валидация контракта v1 -----

def _make_error_event(tick_id, error_code, message, field_path=None):
    """Собрать CONTRACT_ERROR событие."""
    return {
        "contract_version": "v1",
        "event_type": "CONTRACT_ERROR",
        "server_tick": tick_id,
        "payload": {
            "error_code": error_code,
            "message": message,
            "field_path": field_path,
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
            found = False
            for tile in tiles:
                if tile["tile_id"] == tile_id:
                    tile["water_level"] = 100
                    found = True
                    break

            if found:
                events.append({
                    "contract_version": "v1",
                    "event_type": "PLANT_WATERED",
                    "server_tick": tick_id,
                    "payload": {"tile_id": tile_id, "player_id": player_id},
                })
            else:
                events.append(_make_error_event(tick_id, "MISSING_FIELD",
                                                f"Tile not found: {tile_id}"))

        elif action_type == "START_RECIPE":
            factory_id = payload["factory_id"]
            recipe_id = payload["recipe_id"]
            duration_sec = payload["duration_sec"]
            found = False
            for factory in factories:
                if factory["factory_id"] == factory_id:
                    factory["active_recipe_id"] = recipe_id
                    factory["remaining_time_sec"] = duration_sec
                    found = True
                    break

            if found:
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
            else:
                events.append(_make_error_event(tick_id, "MISSING_FIELD",
                                                f"Factory not found: {factory_id}"))

        elif action_type == "PLACE_ON_TILE":
            tile_id = payload["tile_id"]
            plant_id = payload["plant_id"]
            initial_health = payload["initial_health"]
            initial_water = payload["initial_water_level"]

            # Найти клетку
            tile = None
            for t in tiles:
                if t["tile_id"] == tile_id:
                    tile = t
                    break

            if tile is None:
                events.append(_make_error_event(tick_id, "MISSING_FIELD",
                                                f"Tile not found: {tile_id}"))
            elif tile["owner_player_id"] != player_id:
                events.append(_make_error_event(tick_id, "INVALID_TYPE",
                                                f"Tile {tile_id} not owned by {player_id}"))
            elif tile.get("occupant_type") and tile["occupant_type"] != "EMPTY":
                events.append(_make_error_event(tick_id, "INVALID_TYPE",
                                                f"Tile already occupied: {tile_id}"))
            elif tile["zone_type"] != "PLANT":
                events.append(_make_error_event(tick_id, "INVALID_TYPE",
                                                f"Tile zone is {tile['zone_type']}, expected PLANT"))
            else:
                # Проверить инвентарь игрока
                player = None
                for p in next_world_state["players"]:
                    if p["player_id"] == player_id:
                        player = p
                        break

                if player is None:
                    events.append(_make_error_event(tick_id, "MISSING_FIELD",
                                                    f"Player not found: {player_id}"))
                else:
                    inv_found = False
                    for idx, item in enumerate(player["inventory"]):
                        if item["product_id"] == plant_id:
                            if item["amount"] < 1:
                                events.append(_make_error_event(
                                    tick_id, "MISSING_FIELD",
                                    f"No {plant_id} in inventory for player {player_id}"))
                                inv_found = True
                                break

                            # Списать 1 единицу
                            if item["amount"] == 1:
                                del player["inventory"][idx]
                            else:
                                item["amount"] -= 1

                            # Посадить растение
                            tile["occupant_type"] = "PLANT"
                            tile["occupant_id"] = plant_id
                            tile["health"] = initial_health
                            tile["water_level"] = initial_water

                            events.append({
                                "contract_version": "v1",
                                "event_type": "PLANT_PLACED",
                                "server_tick": tick_id,
                                "payload": {
                                    "tile_id": tile_id,
                                    "plant_id": plant_id,
                                    "player_id": player_id,
                                },
                            })
                            inv_found = True
                            break

                    if not inv_found:
                        events.append(_make_error_event(
                            tick_id, "MISSING_FIELD",
                            f"No {plant_id} in inventory for player {player_id}"))

        else:
            events.append(_make_error_event(tick_id, "INVALID_TYPE",
                                            f"Unknown action_type: {action_type}"))

    # Шаг 5: результат
    return {
        "contract_version": "v1",
        "tick_id": tick_id,
        "next_world_state": next_world_state,
        "events": events,
    }
