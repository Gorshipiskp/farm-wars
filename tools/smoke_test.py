r"""
Smoke-тест для engine_core: все checkpoints (001 + 002).

Проверяет:
1. Базовый вызов simulate_tick, валидацию, детерминированность.
2. WATER_PLANT и START_RECIPE.
3. PLACE_ON_TILE: посадка, инвентарь, все ошибки.

Запуск из корня проекта:
    py tools/smoke_test.py
"""

import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

build_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "engine_cpp", "build", "Release")
if os.path.isdir(build_dir):
    sys.path.insert(0, build_dir)


def load_fixture(subdir, name):
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", subdir, name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_simulate():
    """Возвращает simulate_tick: из C++ модуля если собран, иначе из stub."""
    try:
        import engine_core
        return engine_core.simulate_tick
    except ImportError:
        from engine_core_stub.stub import simulate_tick
        return simulate_tick


# ===== Базовые тесты (CP1) =====

def test_basic_tick():
    print("\n--- Test 1: Basic tick (valid input) ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    actions = load_fixture("actions", "actions_water_and_recipe.json")

    tick_input = {
        "contract_version": "v1",
        "tick_id": 5,
        "world_state": world,
        "actions": actions,
    }

    result = sim(tick_input)

    assert result["contract_version"] == "v1"
    assert result["tick_id"] == 5
    assert "next_world_state" in result
    assert "events" in result

    # Детерминированность
    result2 = sim(tick_input)
    assert result == result2, "NOT deterministic!"

    print("  [OK] Basic tick works")
    print(f"  Events: {[e['event_type'] for e in result['events']]}")


# ===== Тесты валидации контракта (CP2) =====

def _check_contract_error(result, expected_code, msg_hint=""):
    """Проверить что результат содержит CONTRACT_ERROR с нужным кодом."""
    events = result["events"]
    contract_errors = [e for e in events if e["event_type"] == "CONTRACT_ERROR"]
    assert len(contract_errors) >= 1, f"Expected CONTRACT_ERROR, got events: {[e['event_type'] for e in events]}"
    error = contract_errors[0]
    assert error["payload"]["error_code"] == expected_code, \
        f"Expected {expected_code}, got {error['payload']['error_code']}: {error['payload']['message']}"
    if msg_hint:
        assert msg_hint in error["payload"]["message"], \
            f"Message '{error['payload']['message']}' should contain '{msg_hint}'"


def test_missing_contract_version():
    print("\n--- Test 2a: Missing contract_version -> CONTRACT_ERROR ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    bad = {"tick_id": 1, "world_state": world, "actions": []}
    result = sim(bad)
    _check_contract_error(result, "MISSING_FIELD", "contract_version")
    print("  [OK]")


def test_wrong_contract_version():
    print("\n--- Test 2b: Wrong contract_version (v99) -> UNSUPPORTED_VERSION ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    bad = {"contract_version": "v99", "tick_id": 1, "world_state": world, "actions": []}
    result = sim(bad)
    _check_contract_error(result, "UNSUPPORTED_VERSION")
    print("  [OK]")


def test_missing_tick_id():
    print("\n--- Test 2c: Missing tick_id -> CONTRACT_ERROR ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    bad = {"contract_version": "v1", "world_state": world, "actions": []}
    result = sim(bad)
    _check_contract_error(result, "MISSING_FIELD", "tick_id")
    print("  [OK]")


def test_missing_world_state():
    print("\n--- Test 2d: Missing world_state entirely -> CONTRACT_ERROR ---")
    sim = get_simulate()
    bad = {"contract_version": "v1", "tick_id": 1, "actions": []}
    result = sim(bad)
    _check_contract_error(result, "MISSING_FIELD", "world_state")
    print("  [OK]")


def test_missing_match_id_in_world_state():
    print("\n--- Test 2e: Missing match_id in world_state -> CONTRACT_ERROR ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    del world["match_id"]
    bad = {"contract_version": "v1", "tick_id": 1, "world_state": world, "actions": []}
    result = sim(bad)
    _check_contract_error(result, "MISSING_FIELD", "match_id")
    print("  [OK]")


def test_missing_player_id_in_action():
    print("\n--- Test 2f: Missing player_id in action -> CONTRACT_ERROR ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    bad = {
        "contract_version": "v1",
        "tick_id": 1,
        "world_state": world,
        "actions": [
            {"contract_version": "v1", "action_type": "WATER_PLANT",
             "payload": {"tile_id": "t1"}, "client_ts": 0}
        ],
    }
    result = sim(bad)
    _check_contract_error(result, "MISSING_FIELD", "player_id")
    print("  [OK]")


def test_unknown_action_type():
    print("\n--- Test 2g: Unknown action_type -> INVALID_TYPE ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    bad = {
        "contract_version": "v1",
        "tick_id": 1,
        "world_state": world,
        "actions": [
            {"contract_version": "v1", "player_id": "p1",
             "action_type": "UNKNOWN_FAKE", "payload": {}, "client_ts": 0}
        ],
    }
    result = sim(bad)
    _check_contract_error(result, "INVALID_TYPE")
    print("  [OK]")


def test_wrong_type_for_tick_id():
    print("\n--- Test 2h: tick_id is string (not number) -> INVALID_TYPE ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    bad = {"contract_version": "v1", "tick_id": "abc", "world_state": world, "actions": []}
    result = sim(bad)
    _check_contract_error(result, "INVALID_TYPE", "tick_id")
    print("  [OK]")


# ===== Тесты детерминированности (CP3) =====

def test_determinism_100_iterations():
    print("\n--- Test 3a: Determinism — 100 iterations, same output ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    actions = load_fixture("actions", "actions_water_and_recipe.json")
    tick_input = {"contract_version": "v1", "tick_id": 42, "world_state": world, "actions": actions}

    first = sim(tick_input)
    for i in range(100):
        current = sim(tick_input)
        assert current == first, f"Iteration {i}: output differs from first!"
    print("  [OK] 100/100 iterations identical")


def test_determinism_no_actions():
    print("\n--- Test 3b: Determinism — empty actions list ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    tick_input = {"contract_version": "v1", "tick_id": 10, "world_state": world, "actions": []}

    first = sim(tick_input)
    for i in range(10):
        assert sim(tick_input) == first, f"Empty actions: iteration {i} differs!"
    print("  [OK]")


def test_input_not_mutated():
    print("\n--- Test 3c: Input dict is NOT mutated by simulate_tick ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    actions = load_fixture("actions", "actions_water_and_recipe.json")
    tick_input = {"contract_version": "v1", "tick_id": 7, "world_state": world, "actions": actions}

    # Глубокая копия ДО вызова, чтобы сравнить после
    original = copy.deepcopy(tick_input)

    sim(tick_input)

    assert tick_input == original, "simulate_tick mutated the input dict! (side effect detected)"
    print("  [OK] Input untouched after call")


def test_determinism_different_tick_ids():
    print("\n--- Test 3d: Different tick_ids — world_state.tick_id updated correctly ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")

    for tid in [1, 5, 100, 999]:
        tick_input = {"contract_version": "v1", "tick_id": tid, "world_state": world, "actions": []}
        result = sim(tick_input)
        assert result["tick_id"] == tid, f"result.tick_id should be {tid}, got {result['tick_id']}"
        assert result["next_world_state"]["tick_id"] == tid, \
            f"next_world_state.tick_id should be {tid}, got {result['next_world_state']['tick_id']}"

    print("  [OK] tick_id correctly propagated for 4 values")


# ===== Тесты обработки действий (CP4) =====

def test_water_plant_changes_water_level():
    print("\n--- Test 4a: WATER_PLANT sets water_level to 100 ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")

    # Исходный water_level для tile t1 = 30
    orig = world["map"]["tiles"][0]
    assert orig["tile_id"] == "t1"
    assert orig["water_level"] == 30

    tick_input = {
        "contract_version": "v1",
        "tick_id": 5,
        "world_state": world,
        "actions": [{
            "contract_version": "v1", "player_id": "p1",
            "action_type": "WATER_PLANT",
            "payload": {"tile_id": "t1"}, "client_ts": 0
        }],
    }

    result = sim(tick_input)
    new_tile = result["next_world_state"]["map"]["tiles"][0]
    assert new_tile["tile_id"] == "t1"
    assert new_tile["water_level"] == 100, f"Expected 100, got {new_tile['water_level']}"

    # Исходный мир НЕ изменился
    assert world["map"]["tiles"][0]["water_level"] == 30, "Original world was mutated!"

    print("  [OK] water_level: 30 -> 100, original untouched")


def test_water_plant_generates_event():
    print("\n--- Test 4b: WATER_PLANT generates PLANT_WATERED event ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    tick_input = {
        "contract_version": "v1", "tick_id": 1,
        "world_state": world,
        "actions": [{
            "contract_version": "v1", "player_id": "p1",
            "action_type": "WATER_PLANT",
            "payload": {"tile_id": "t1"}, "client_ts": 0
        }],
    }

    result = sim(tick_input)
    events = result["events"]
    assert len(events) == 1
    ev = events[0]
    assert ev["event_type"] == "PLANT_WATERED"
    assert ev["payload"]["tile_id"] == "t1"
    assert ev["payload"]["player_id"] == "p1"
    assert ev["server_tick"] == 1
    print("  [OK] PLANT_WATERED event: tile=t1 player=p1 tick=1")


def test_water_plant_tile_not_found():
    print("\n--- Test 4c: WATER_PLANT on missing tile -> CONTRACT_ERROR ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    tick_input = {
        "contract_version": "v1", "tick_id": 1,
        "world_state": world,
        "actions": [{
            "contract_version": "v1", "player_id": "p1",
            "action_type": "WATER_PLANT",
            "payload": {"tile_id": "nonexistent_zzz"}, "client_ts": 0
        }],
    }

    result = sim(tick_input)
    _check_contract_error(result, "MISSING_FIELD", "Tile not found")
    print("  [OK] Missing tile returns CONTRACT_ERROR")


def test_start_recipe_sets_factory():
    print("\n--- Test 4d: START_RECIPE sets factory state ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")

    # Исходно завод простаивает
    orig = world["factories"][0]
    assert orig["factory_id"] == "bakery_1"
    assert orig["active_recipe_id"] is None
    assert orig["remaining_time_sec"] == 0

    tick_input = {
        "contract_version": "v1", "tick_id": 10,
        "world_state": world,
        "actions": [{
            "contract_version": "v1", "player_id": "p1",
            "action_type": "START_RECIPE",
            "payload": {"factory_id": "bakery_1", "recipe_id": "bread", "duration_sec": 30},
            "client_ts": 0
        }],
    }

    result = sim(tick_input)
    factory = result["next_world_state"]["factories"][0]
    assert factory["active_recipe_id"] == "bread"
    assert factory["remaining_time_sec"] == 30

    # Исходный мир не изменился
    assert world["factories"][0]["active_recipe_id"] is None, "Original world mutated!"
    print("  [OK] Factory: recipe=bread, remaining=30s, original untouched")


def test_start_recipe_generates_event():
    print("\n--- Test 4e: START_RECIPE generates RECIPE_STARTED event ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    tick_input = {
        "contract_version": "v1", "tick_id": 99,
        "world_state": world,
        "actions": [{
            "contract_version": "v1", "player_id": "p1",
            "action_type": "START_RECIPE",
            "payload": {"factory_id": "bakery_1", "recipe_id": "cake", "duration_sec": 60},
            "client_ts": 0
        }],
    }

    result = sim(tick_input)
    ev = result["events"][0]
    assert ev["event_type"] == "RECIPE_STARTED"
    assert ev["payload"]["factory_id"] == "bakery_1"
    assert ev["payload"]["recipe_id"] == "cake"
    assert ev["payload"]["player_id"] == "p1"
    assert ev["server_tick"] == 99
    print("  [OK] RECIPE_STARTED event: bakery_1 cake p1 tick=99")


def test_start_recipe_factory_not_found():
    print("\n--- Test 4f: START_RECIPE on missing factory -> CONTRACT_ERROR ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    tick_input = {
        "contract_version": "v1", "tick_id": 1,
        "world_state": world,
        "actions": [{
            "contract_version": "v1", "player_id": "p1",
            "action_type": "START_RECIPE",
            "payload": {"factory_id": "nonexistent_zzz", "recipe_id": "x", "duration_sec": 10},
            "client_ts": 0
        }],
    }

    result = sim(tick_input)
    _check_contract_error(result, "MISSING_FIELD", "Factory not found")
    print("  [OK] Missing factory returns CONTRACT_ERROR")


def test_multiple_actions():
    print("\n--- Test 4g: Two WATER_PLANT + one START_RECIPE in single tick ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    tick_input = {
        "contract_version": "v1", "tick_id": 42,
        "world_state": world,
        "actions": [
            {"contract_version": "v1", "player_id": "p1",
             "action_type": "WATER_PLANT", "payload": {"tile_id": "t1"}, "client_ts": 0},
            {"contract_version": "v1", "player_id": "p1",
             "action_type": "WATER_PLANT", "payload": {"tile_id": "t2"}, "client_ts": 0},
            {"contract_version": "v1", "player_id": "p1",
             "action_type": "START_RECIPE",
             "payload": {"factory_id": "bakery_1", "recipe_id": "bread", "duration_sec": 30},
             "client_ts": 0},
        ],
    }

    result = sim(tick_input)
    events = result["events"]
    event_types = [e["event_type"] for e in events]
    assert event_types == ["PLANT_WATERED", "PLANT_WATERED", "RECIPE_STARTED"], \
        f"Wrong event order: {event_types}"

    nws = result["next_world_state"]
    assert nws["map"]["tiles"][0]["water_level"] == 100  # t1 полита
    assert nws["map"]["tiles"][1]["water_level"] == 100  # t2 полита
    assert nws["factories"][0]["active_recipe_id"] == "bread"

    print("  [OK] 3 actions -> 3 events, both tiles watered, factory started")


# ===== Тесты PLACE_ON_TILE (CP2-CP4) =====

def test_place_on_tile_basic():
    print("\n--- Test 5a: PLACE_ON_TILE on empty PLANT tile ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")

    # Исходно t3 пустая, инвентарь: wheat x3
    assert len(world["players"][0]["inventory"]) == 2
    assert world["players"][0]["inventory"][0]["amount"] == 3  # wheat

    tick_input = {
        "contract_version": "v1", "tick_id": 5,
        "world_state": world,
        "actions": [{
            "contract_version": "v1", "player_id": "p1",
            "action_type": "PLACE_ON_TILE",
            "payload": {"tile_id": "t3", "plant_id": "wheat",
                        "initial_health": 100, "initial_water_level": 50},
            "client_ts": 0
        }],
    }

    result = sim(tick_input)

    # Проверка события
    events = result["events"]
    assert len(events) == 1
    assert events[0]["event_type"] == "PLANT_PLACED"
    assert events[0]["payload"]["tile_id"] == "t3"
    assert events[0]["payload"]["plant_id"] == "wheat"

    # Проверка состояния клетки
    tile = result["next_world_state"]["map"]["tiles"][2]  # t3
    assert tile["tile_id"] == "t3"
    assert tile["occupant_type"] == "PLANT"
    assert tile["occupant_id"] == "wheat"
    assert tile["health"] == 100
    assert tile["water_level"] == 50

    # Проверка инвентаря: wheat было 3, стало 2
    inv = result["next_world_state"]["players"][0]["inventory"]
    wheat_item = next(i for i in inv if i["product_id"] == "wheat")
    assert wheat_item["amount"] == 2

    # Исходный мир не мутирован
    assert world["map"]["tiles"][2]["occupant_type"] == "EMPTY"
    assert world["players"][0]["inventory"][0]["amount"] == 3

    print("  [OK] Wheat planted on t3, inventory: 3 -> 2")


def test_place_on_tile_last_seed():
    print("\n--- Test 5b: PLACE_ON_TILE with last seed (amount=1) -> removed from inventory ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")

    # corn в инвентаре только 1 штука
    tick_input = {
        "contract_version": "v1", "tick_id": 5,
        "world_state": world,
        "actions": [{
            "contract_version": "v1", "player_id": "p1",
            "action_type": "PLACE_ON_TILE",
            "payload": {"tile_id": "t3", "plant_id": "corn",
                        "initial_health": 100, "initial_water_level": 40},
            "client_ts": 0
        }],
    }

    result = sim(tick_input)
    inv = result["next_world_state"]["players"][0]["inventory"]

    # corn должен исчезнуть из инвентаря
    corn_items = [i for i in inv if i["product_id"] == "corn"]
    assert len(corn_items) == 0, f"Corn should be removed, got {corn_items}"

    # wheat остался нетронутым
    wheat_items = [i for i in inv if i["product_id"] == "wheat"]
    assert wheat_items[0]["amount"] == 3

    print("  [OK] Last corn used, removed from inventory")


def test_place_on_tile_occupied():
    print("\n--- Test 5c: PLACE_ON_TILE on occupied tile -> CONTRACT_ERROR ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")

    # t1 уже занята (occupant_type = "PLANT")
    tick_input = {
        "contract_version": "v1", "tick_id": 5,
        "world_state": world,
        "actions": [{
            "contract_version": "v1", "player_id": "p1",
            "action_type": "PLACE_ON_TILE",
            "payload": {"tile_id": "t1", "plant_id": "wheat",
                        "initial_health": 100, "initial_water_level": 50},
            "client_ts": 0
        }],
    }

    result = sim(tick_input)
    _check_contract_error(result, "INVALID_TYPE", "already occupied")
    print("  [OK]")


def test_place_on_tile_wrong_zone():
    print("\n--- Test 5d: PLACE_ON_TILE on ANIMAL zone -> CONTRACT_ERROR ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")

    # t4 - ANIMAL зона
    tick_input = {
        "contract_version": "v1", "tick_id": 5,
        "world_state": world,
        "actions": [{
            "contract_version": "v1", "player_id": "p1",
            "action_type": "PLACE_ON_TILE",
            "payload": {"tile_id": "t4", "plant_id": "wheat",
                        "initial_health": 100, "initial_water_level": 50},
            "client_ts": 0
        }],
    }

    result = sim(tick_input)
    _check_contract_error(result, "INVALID_TYPE", "expected PLANT")
    print("  [OK]")


def test_place_on_tile_no_inventory():
    print("\n--- Test 5e: PLACE_ON_TILE with no seeds -> CONTRACT_ERROR ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")

    # potato нет в инвентаре
    tick_input = {
        "contract_version": "v1", "tick_id": 5,
        "world_state": world,
        "actions": [{
            "contract_version": "v1", "player_id": "p1",
            "action_type": "PLACE_ON_TILE",
            "payload": {"tile_id": "t3", "plant_id": "potato",
                        "initial_health": 100, "initial_water_level": 60},
            "client_ts": 0
        }],
    }

    result = sim(tick_input)
    _check_contract_error(result, "MISSING_FIELD", "No potato")
    print("  [OK]")


def test_place_on_tile_not_owned():
    print("\n--- Test 5f: PLACE_ON_TILE on other player's tile -> CONTRACT_ERROR ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")

    # p2 пытается посадить на t3 (принадлежит p1)
    tick_input = {
        "contract_version": "v1", "tick_id": 5,
        "world_state": world,
        "actions": [{
            "contract_version": "v1", "player_id": "p2",
            "action_type": "PLACE_ON_TILE",
            "payload": {"tile_id": "t3", "plant_id": "wheat",
                        "initial_health": 100, "initial_water_level": 50},
            "client_ts": 0
        }],
    }

    result = sim(tick_input)
    _check_contract_error(result, "INVALID_TYPE", "not owned")
    print("  [OK]")


def test_place_on_tile_nonexistent():
    print("\n--- Test 5g: PLACE_ON_TILE on nonexistent tile -> CONTRACT_ERROR ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")

    tick_input = {
        "contract_version": "v1", "tick_id": 5,
        "world_state": world,
        "actions": [{
            "contract_version": "v1", "player_id": "p1",
            "action_type": "PLACE_ON_TILE",
            "payload": {"tile_id": "nonexistent_zzz", "plant_id": "wheat",
                        "initial_health": 100, "initial_water_level": 50},
            "client_ts": 0
        }],
    }

    result = sim(tick_input)
    _check_contract_error(result, "MISSING_FIELD", "Tile not found")
    print("  [OK]")


def test_place_on_tile_three_in_row():
    print("\n--- Test 5h: Three PLACE_ON_TILE in a row (inventory: 3 -> 2 -> 1 -> 0) ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")

    # Первый: сажаем wheat на t3
    r1 = sim({"contract_version": "v1", "tick_id": 1, "world_state": world, "actions": [{
        "contract_version": "v1", "player_id": "p1", "action_type": "PLACE_ON_TILE",
        "payload": {"tile_id": "t3", "plant_id": "wheat", "initial_health": 100, "initial_water_level": 50},
        "client_ts": 0
    }]})
    inv1 = r1["next_world_state"]["players"][0]["inventory"]
    assert [i for i in inv1 if i["product_id"] == "wheat"][0]["amount"] == 2

    # Второй: используем состояние из r1
    r2 = sim({"contract_version": "v1", "tick_id": 2, "world_state": r1["next_world_state"], "actions": [{
        "contract_version": "v1", "player_id": "p1", "action_type": "PLACE_ON_TILE",
        "payload": {"tile_id": "t3", "plant_id": "wheat", "initial_health": 100, "initial_water_level": 50},
        "client_ts": 0
    }]})
    inv2 = r2["next_world_state"]["players"][0]["inventory"]
    # t3 уже занята — должно быть CONTRACT_ERROR, инвентарь НЕ изменился
    assert [i for i in inv2 if i["product_id"] == "wheat"][0]["amount"] == 2, \
        "Inventory should NOT change on failed placement"

    # Третий: используем оригинал, сажаем corn (1 шт)
    r3 = sim({"contract_version": "v1", "tick_id": 3, "world_state": world, "actions": [{
        "contract_version": "v1", "player_id": "p1", "action_type": "PLACE_ON_TILE",
        "payload": {"tile_id": "t3", "plant_id": "corn", "initial_health": 100, "initial_water_level": 40},
        "client_ts": 0
    }]})
    inv3 = r3["next_world_state"]["players"][0]["inventory"]
    corn_items = [i for i in inv3 if i["product_id"] == "corn"]
    assert len(corn_items) == 0  # исчез

    print("  [OK] 3 placements: inventory tracked correctly, errors don't consume items")


# ===== Сравнение stub vs C++ =====

def test_stub_vs_cpp():
    print("\n--- Test 3: Stub vs C++ comparison ---")

    try:
        import engine_core
        cpp_sim = engine_core.simulate_tick
    except ImportError:
        print("  [SKIP] C++ module not built")
        return

    from engine_core_stub.stub import simulate_tick as stub_sim

    world = load_fixture("world_state", "minimal_world.json")
    actions = load_fixture("actions", "actions_water_and_recipe.json")
    tick_input = {"contract_version": "v1", "tick_id": 5, "world_state": world, "actions": actions}

    cpp_result = cpp_sim(tick_input)
    stub_result = stub_sim(tick_input)

    assert cpp_result == stub_result, "CPP and STUB outputs DIFFER!"
    print("  [OK] Stub and C++ outputs are IDENTICAL")

    # Сравниваем и для ошибок валидации
    bad = {"contract_version": "v99", "tick_id": 1, "world_state": world, "actions": []}
    assert cpp_sim(bad) == stub_sim(bad), "CPP and STUB differ on validation errors!"
    print("  [OK] Validation errors also match")


# ===== Main =====

def main():
    print("=" * 60)
    print("SMOKE TEST — engine_core (CP 1-4 + PLACE_ON_TILE)")
    print("=" * 60)

    test_basic_tick()
    test_missing_contract_version()
    test_wrong_contract_version()
    test_missing_tick_id()
    test_missing_world_state()
    test_missing_match_id_in_world_state()
    test_missing_player_id_in_action()
    test_unknown_action_type()
    test_wrong_type_for_tick_id()
    test_determinism_100_iterations()
    test_determinism_no_actions()
    test_input_not_mutated()
    test_determinism_different_tick_ids()
    test_water_plant_changes_water_level()
    test_water_plant_generates_event()
    test_water_plant_tile_not_found()
    test_start_recipe_sets_factory()
    test_start_recipe_generates_event()
    test_start_recipe_factory_not_found()
    test_multiple_actions()
    test_place_on_tile_basic()
    test_place_on_tile_last_seed()
    test_place_on_tile_occupied()
    test_place_on_tile_wrong_zone()
    test_place_on_tile_no_inventory()
    test_place_on_tile_not_owned()
    test_place_on_tile_nonexistent()
    test_place_on_tile_three_in_row()
    test_stub_vs_cpp()

    print("\n" + "=" * 60)
    print("ALL CHECKS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
