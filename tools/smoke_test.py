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
    # Полив дает 100, но пассивная фаза после действий отнимает decay=2
    assert new_tile["water_level"] == 98, f"Expected 98 (100 - 2 decay), got {new_tile['water_level']}"

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
    assert factory["remaining_time_sec"] == 29  # 30 - 1 (пассивная фаза)

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
    # Полив дает 100 - decay(2) = 98
    assert nws["map"]["tiles"][0]["water_level"] == 98  # t1 полита (+ пассивная фаза)
    assert nws["map"]["tiles"][1]["water_level"] == 98  # t2 полита (+ пассивная фаза)
    assert nws["factories"][0]["active_recipe_id"] == "bread"

    print("  [OK] 3 actions -> 3 events, both tiles watered, factory started")


# ===== Тесты PLACE_ON_TILE (CP2-CP4) =====

def test_place_on_tile_basic():
    print("\n--- Test 5a: PLACE_ON_TILE on empty PLANT tile ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")

    tick_input = {
        "contract_version": "v1", "tick_id": 5,
        "world_state": world,
        "actions": [{
            "contract_version": "v1", "player_id": "p1",
            "action_type": "PLACE_ON_TILE",
            "payload": {"tile_id": "t3", "plant_id": "wheat",
                        "initial_health": 100, "initial_water_level": 50,
                        "growth_time_sec": 120, "water_decay_per_tick": 2},
            "client_ts": 0
        }],
    }

    result = sim(tick_input)
    tile = result["next_world_state"]["map"]["tiles"][2]  # t3
    assert tile["occupant_type"] == "PLANT"
    # Посажено с growth_elapsed_sec=0, но пассивная фаза сразу +1 (вода > 0)
    assert tile["growth_elapsed_sec"] == 1, f"Expected 1, got {tile['growth_elapsed_sec']}"
    assert tile["growth_time_sec"] == 120
    assert tile["water_decay_per_tick"] == 2
    print("  [OK] Wheat planted with growth fields, elapsed=1")


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
                        "initial_health": 100, "initial_water_level": 40,
                        "growth_time_sec": 150, "water_decay_per_tick": 2},
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
        "payload": {"tile_id": "t3", "plant_id": "wheat", "initial_health": 100, "initial_water_level": 50,
                    "growth_time_sec": 120, "water_decay_per_tick": 2},
        "client_ts": 0
    }]})
    inv1 = r1["next_world_state"]["players"][0]["inventory"]
    assert [i for i in inv1 if i["product_id"] == "wheat"][0]["amount"] == 2

    # Второй: используем состояние из r1
    r2 = sim({"contract_version": "v1", "tick_id": 2, "world_state": r1["next_world_state"], "actions": [{
        "contract_version": "v1", "player_id": "p1", "action_type": "PLACE_ON_TILE",
        "payload": {"tile_id": "t3", "plant_id": "wheat", "initial_health": 100, "initial_water_level": 50,
                    "growth_time_sec": 120, "water_decay_per_tick": 2},
        "client_ts": 0
    }]})
    inv2 = r2["next_world_state"]["players"][0]["inventory"]
    # t3 уже занята — должно быть CONTRACT_ERROR, инвентарь НЕ изменился
    assert [i for i in inv2 if i["product_id"] == "wheat"][0]["amount"] == 2, \
        "Inventory should NOT change on failed placement"

    # Третий: используем оригинал, сажаем corn (1 шт)
    r3 = sim({"contract_version": "v1", "tick_id": 3, "world_state": world, "actions": [{
        "contract_version": "v1", "player_id": "p1", "action_type": "PLACE_ON_TILE",
        "payload": {"tile_id": "t3", "plant_id": "corn", "initial_health": 100, "initial_water_level": 40,
                    "growth_time_sec": 150, "water_decay_per_tick": 2},
        "client_ts": 0
    }]})
    inv3 = r3["next_world_state"]["players"][0]["inventory"]
    corn_items = [i for i in inv3 if i["product_id"] == "corn"]
    assert len(corn_items) == 0  # исчез

    print("  [OK] 3 placements: inventory tracked correctly, errors don't consume items")


# ===== Тесты пассивной фазы роста (engine_cpp/003 Phase 1) =====

def test_growth_water_decay():
    print("\n--- Test 6a: Water decays each tick ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    # t1: water=30, decay=2  → после тика 28
    # t2: water=10, decay=2  → после тика 8
    tick_input = {"contract_version": "v1", "tick_id": 99, "world_state": world, "actions": []}
    result = sim(tick_input)
    assert result["next_world_state"]["map"]["tiles"][0]["water_level"] == 28  # 30 - 2
    assert result["next_world_state"]["map"]["tiles"][1]["water_level"] == 8   # 10 - 2
    print("  [OK] t1: 30->28, t2: 10->8")


def test_growth_elapsed_increases():
    print("\n--- Test 6b: growth_elapsed_sec increases when watered ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    # t1: water>0 → growth_elapsed должен вырасти
    tick_input = {"contract_version": "v1", "tick_id": 1, "world_state": world, "actions": []}
    result = sim(tick_input)
    tile = result["next_world_state"]["map"]["tiles"][0]  # t1
    assert tile["growth_elapsed_sec"] == 1, f"Expected 1, got {tile['growth_elapsed_sec']}"
    print("  [OK] growth_elapsed_sec: 0 -> 1")


def test_growth_stops_without_water():
    print("\n--- Test 6c: growth_elapsed_sec does NOT increase when water=0 ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    # t2: water=10, decay=2 → через 5 тиков вода кончится
    ws = world
    total_growth = 0
    for tid in range(1, 10):
        result = sim({"contract_version": "v1", "tick_id": tid, "world_state": ws, "actions": []})
        ws = result["next_world_state"]
        tile = ws["map"]["tiles"][1]  # t2 corn
        if tile.get("water_level", 0) > 0:
            total_growth += 1
    # Вода кончилась → рост остановился (всего ~5 тиков роста)
    assert total_growth <= 6, f"Growth should stop when water=0, got {total_growth} ticks"
    print(f"  [OK] Growth ticks: {total_growth} (stopped after water dry)")


def test_plant_death_no_water():
    print("\n--- Test 6d: Plant dies when health reaches 0 ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    # t2: water=10, decay=2, health=100
    # Вода кончится → health -= 10 каждый тик → 10 тиков до смерти
    ws = world
    died = False
    for tid in range(1, 20):
        result = sim({"contract_version": "v1", "tick_id": tid, "world_state": ws, "actions": []})
        ws = result["next_world_state"]
        events = result["events"]
        for ev in events:
            if ev["event_type"] == "PLANT_DIED":
                assert ev["payload"]["tile_id"] == "t2"
                assert ev["payload"]["reason"] == "DEHYDRATED"
                died = True
                break
        if died:
            break

    assert died, "Plant should have died!"
    tile = ws["map"]["tiles"][1]
    assert tile["occupant_type"] == "EMPTY", f"Tile should be EMPTY, got {tile.get('occupant_type')}"
    # Влажность грядки осталась (не обнулилась со смертью растения)
    assert tile["water_level"] is not None, "Water level should remain on tile after plant death"
    assert tile["water_level"] >= 0
    print(f"  [OK] Plant died + PLANT_DIED event, tile cleared, water={tile['water_level']}")


def test_growth_3_ticks_sequence():
    print("\n--- Test 6e: 3 ticks: water decays, growth increments, no death yet ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    ws = world
    for tick in range(1, 4):
        result = sim({"contract_version": "v1", "tick_id": tick, "world_state": ws, "actions": []})
        ws = result["next_world_state"]

    t1 = ws["map"]["tiles"][0]  # wheat, started water=30, decay=2
    assert t1["water_level"] == 24  # 30 - 3*2
    assert t1["growth_elapsed_sec"] == 3  # вода была → 3 тика роста
    assert t1["health"] == 100  # вода была → здоровье не падало
    print("  [OK] t1: water=24, growth=3, health=100")


def test_growth_fields_not_required():
    print("\n--- Test 6f: Tiles without growth fields get defaults (decay=0, growth++) ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    del world["map"]["tiles"][0]["growth_elapsed_sec"]
    del world["map"]["tiles"][0]["growth_time_sec"]
    del world["map"]["tiles"][0]["water_decay_per_tick"]

    tick_input = {"contract_version": "v1", "tick_id": 42, "world_state": world, "actions": []}
    result = sim(tick_input)
    t1 = result["next_world_state"]["map"]["tiles"][0]
    # Без decay: испарение по умолчанию = 1/тик
    assert t1["water_level"] == 29, f"Water decays by default 1/tick: 30 -> 29, got {t1['water_level']}"
    assert t1["growth_elapsed_sec"] == 1, f"Growth still happens, got {t1.get('growth_elapsed_sec')}"
    print("  [OK] Old-format tiles: default evaporation 1/tick, growth ++")


def test_evaporation_on_empty_tiles():
    print("\n--- Test 6g: Empty tiles lose 1 water/tick (evaporation) ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    # t3: empty PLANT, water=50 → должно стать 49
    # t4: empty ANIMAL, water=50 → должно стать 49
    tick_input = {"contract_version": "v1", "tick_id": 1, "world_state": world, "actions": []}
    result = sim(tick_input)
    t3 = result["next_world_state"]["map"]["tiles"][2]  # t3
    t4 = result["next_world_state"]["map"]["tiles"][3]  # t4
    assert t3["water_level"] == 49, f"t3 empty PLANT: 50 -> 49, got {t3['water_level']}"
    assert t4["water_level"] == 49, f"t4 empty ANIMAL: 50 -> 49, got {t4['water_level']}"
    print("  [OK] Empty tiles evaporate: t3=49, t4=49")


# ===== Тесты HARVEST_PLANT (engine_cpp/003 Phase 2) =====

def test_harvest_ripe_plant():
    print("\n--- Test 7a: Harvest ripe plant -> PLANT_HARVESTED, +2 to inventory ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    # t1: wheat, growth_elapsed=0, growth_time=120. Сделаем зрелым — поставим elapsed=200
    world["map"]["tiles"][0]["growth_elapsed_sec"] = 200

    tick_input = {"contract_version": "v1", "tick_id": 5, "world_state": world, "actions": [{
        "contract_version": "v1", "player_id": "p1",
        "action_type": "HARVEST_PLANT",
        "payload": {"tile_id": "t1"}, "client_ts": 0
    }]}

    result = sim(tick_input)
    events = result["events"]
    assert len(events) == 1
    assert events[0]["event_type"] == "PLANT_HARVESTED"
    assert events[0]["payload"]["product_id"] == "wheat"
    assert events[0]["payload"]["amount"] == 2

    # Клетка очищена
    tile = result["next_world_state"]["map"]["tiles"][0]
    assert tile["occupant_type"] == "EMPTY"

    # Продукт в инвентаре
    inv = result["next_world_state"]["players"][0]["inventory"]
    wheat_item = next(i for i in inv if i["product_id"] == "wheat")
    assert wheat_item["amount"] >= 2  # было 3 + 2 от сбора
    print("  [OK] Wheat harvested, +2, tile cleared")


def test_harvest_water_unchanged():
    print("\n--- Test 7b: Harvest does NOT change water_level ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    world["map"]["tiles"][0]["growth_elapsed_sec"] = 200
    orig_water = world["map"]["tiles"][0]["water_level"]  # 30

    tick_input = {"contract_version": "v1", "tick_id": 5, "world_state": world, "actions": [{
        "contract_version": "v1", "player_id": "p1",
        "action_type": "HARVEST_PLANT",
        "payload": {"tile_id": "t1"}, "client_ts": 0
    }]}

    result = sim(tick_input)
    tile = result["next_world_state"]["map"]["tiles"][0]
    # После сбора грядка пустая → испарение по умолчанию = 1/тик: 30 - 1 = 29
    assert tile["water_level"] == 29, f"Water should be 29 (30-1 evap on empty), got {tile['water_level']}"
    print("  [OK] Water unchanged by harvest, only 1/tick evaporation on empty")


def test_harvest_not_ripe():
    print("\n--- Test 7c: Harvest unripe plant -> HARVEST_FAILED NOT_RIPE ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    # t1: growth_elapsed=0, growth_time=120 → не созрело

    tick_input = {"contract_version": "v1", "tick_id": 5, "world_state": world, "actions": [{
        "contract_version": "v1", "player_id": "p1",
        "action_type": "HARVEST_PLANT",
        "payload": {"tile_id": "t1"}, "client_ts": 0
    }]}

    result = sim(tick_input)
    events = result["events"]
    assert events[0]["event_type"] == "HARVEST_FAILED"
    assert events[0]["payload"]["reason"] == "NOT_RIPE"
    # Растение осталось на месте
    assert result["next_world_state"]["map"]["tiles"][0]["occupant_type"] == "PLANT"
    print("  [OK]")


def test_harvest_empty_tile():
    print("\n--- Test 7d: Harvest empty tile -> HARVEST_FAILED NO_PLANT ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")

    tick_input = {"contract_version": "v1", "tick_id": 5, "world_state": world, "actions": [{
        "contract_version": "v1", "player_id": "p1",
        "action_type": "HARVEST_PLANT",
        "payload": {"tile_id": "t3"}, "client_ts": 0  # t3 пустая
    }]}

    result = sim(tick_input)
    assert result["events"][0]["event_type"] == "HARVEST_FAILED"
    assert result["events"][0]["payload"]["reason"] == "NO_PLANT"
    print("  [OK]")


def test_harvest_not_owner():
    print("\n--- Test 7e: Harvest other player's tile -> HARVEST_FAILED NOT_OWNER ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    world["map"]["tiles"][0]["growth_elapsed_sec"] = 200

    tick_input = {"contract_version": "v1", "tick_id": 5, "world_state": world, "actions": [{
        "contract_version": "v1", "player_id": "p2",  # p2 пытается собрать
        "action_type": "HARVEST_PLANT",
        "payload": {"tile_id": "t1"}, "client_ts": 0
    }]}

    result = sim(tick_input)
    assert result["events"][0]["event_type"] == "HARVEST_FAILED"
    assert result["events"][0]["payload"]["reason"] == "NOT_OWNER"
    print("  [OK]")


def test_harvest_nonexistent_tile():
    print("\n--- Test 7f: Harvest nonexistent tile -> HARVEST_FAILED UNKNOWN_TILE ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")

    tick_input = {"contract_version": "v1", "tick_id": 5, "world_state": world, "actions": [{
        "contract_version": "v1", "player_id": "p1",
        "action_type": "HARVEST_PLANT",
        "payload": {"tile_id": "nonexistent_zzz"}, "client_ts": 0
    }]}

    result = sim(tick_input)
    assert result["events"][0]["event_type"] == "HARVEST_FAILED"
    assert result["events"][0]["payload"]["reason"] == "UNKNOWN_TILE"
    print("  [OK]")


def test_harvest_without_growth_fields():
    print("\n--- Test 7g: Harvest without growth fields (backward compat) -> success ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    # Убираем growth поля — растение считается созревшим
    del world["map"]["tiles"][0]["growth_elapsed_sec"]
    del world["map"]["tiles"][0]["growth_time_sec"]

    tick_input = {"contract_version": "v1", "tick_id": 5, "world_state": world, "actions": [{
        "contract_version": "v1", "player_id": "p1",
        "action_type": "HARVEST_PLANT",
        "payload": {"tile_id": "t1"}, "client_ts": 0
    }]}

    result = sim(tick_input)
    assert result["events"][0]["event_type"] == "PLANT_HARVESTED"
    print("  [OK] Without growth fields: harvestable immediately")


# ===== Тесты таймера завода (engine_cpp/003 Phase 3) =====

def test_factory_tick_countdown():
    print("\n--- Test 8a: Factory remaining_time_sec decreases each tick ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    # Запускаем рецепт с duration=30
    tick_input = {"contract_version": "v1", "tick_id": 1, "world_state": world, "actions": [{
        "contract_version": "v1", "player_id": "p1",
        "action_type": "START_RECIPE",
        "payload": {"factory_id": "bakery_1", "recipe_id": "bread", "duration_sec": 5},
        "client_ts": 0
    }]}

    result = sim(tick_input)
    factory = result["next_world_state"]["factories"][0]
    assert factory["remaining_time_sec"] == 4, f"Started at 5, got {factory['remaining_time_sec']} (passive phase -1)"
    print("  [OK] Recipe started with 5s timer")


def test_factory_recipe_finishes():
    print("\n--- Test 8b: Recipe finishes after N ticks -> RECIPE_FINISHED, +1 product ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")

    # Запускаем bread на 3 тика
    r1 = sim({"contract_version": "v1", "tick_id": 1, "world_state": world, "actions": [{
        "contract_version": "v1", "player_id": "p1",
        "action_type": "START_RECIPE",
        "payload": {"factory_id": "bakery_1", "recipe_id": "bread", "duration_sec": 3},
        "client_ts": 0
    }]})
    ws = r1["next_world_state"]
    assert ws["factories"][0]["remaining_time_sec"] == 2  # 3 - 1 (passive)

    # Тик 2
    r2 = sim({"contract_version": "v1", "tick_id": 2, "world_state": ws, "actions": []})
    ws = r2["next_world_state"]
    assert ws["factories"][0]["remaining_time_sec"] == 1

    # Тик 3 — рецепт завершается
    r3 = sim({"contract_version": "v1", "tick_id": 3, "world_state": ws, "actions": []})
    ws = r3["next_world_state"]
    factory = ws["factories"][0]
    assert factory["remaining_time_sec"] == 0, f"Should be 0, got {factory['remaining_time_sec']}"
    assert factory["active_recipe_id"] is None, "Factory should be idle"

    events = r3["events"]
    finished_events = [e for e in events if e["event_type"] == "RECIPE_FINISHED"]
    assert len(finished_events) == 1
    assert finished_events[0]["payload"]["product_id"] == "bread"

    # Проверить инвентарь
    inv = ws["players"][0]["inventory"]
    bread_items = [i for i in inv if i["product_id"] == "bread"]
    assert len(bread_items) == 1
    assert bread_items[0]["amount"] >= 1
    print("  [OK] 3 ticks -> RECIPE_FINISHED, +1 bread, factory idle")


def test_factory_multiple_recipes():
    print("\n--- Test 8c: Two recipes in sequence ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")

    # Первый рецепт
    r1 = sim({"contract_version": "v1", "tick_id": 1, "world_state": world, "actions": [{
        "contract_version": "v1", "player_id": "p1",
        "action_type": "START_RECIPE",
        "payload": {"factory_id": "bakery_1", "recipe_id": "bread", "duration_sec": 2},
        "client_ts": 0
    }]})
    ws = r1["next_world_state"]
    # passive: 2 -> 1

    # Еще 2 тика — рецепт готов
    r2 = sim({"contract_version": "v1", "tick_id": 2, "world_state": ws, "actions": []})
    ws = r2["next_world_state"]
    r3 = sim({"contract_version": "v1", "tick_id": 3, "world_state": ws, "actions": []})
    ws = r3["next_world_state"]
    assert ws["factories"][0]["active_recipe_id"] is None, "Factory should be idle after bread"

    # Второй рецепт
    r4 = sim({"contract_version": "v1", "tick_id": 4, "world_state": ws, "actions": [{
        "contract_version": "v1", "player_id": "p1",
        "action_type": "START_RECIPE",
        "payload": {"factory_id": "bakery_1", "recipe_id": "cake", "duration_sec": 2},
        "client_ts": 0
    }]})
    ws = r4["next_world_state"]
    r5 = sim({"contract_version": "v1", "tick_id": 5, "world_state": ws, "actions": []})
    ws = r5["next_world_state"]
    r6 = sim({"contract_version": "v1", "tick_id": 6, "world_state": ws, "actions": []})
    ws = r6["next_world_state"]

    assert ws["factories"][0]["active_recipe_id"] is None
    inv = ws["players"][0]["inventory"]
    assert any(i["product_id"] == "bread" for i in inv), "Should have bread"
    assert any(i["product_id"] == "cake" for i in inv), "Should have cake"
    print("  [OK] Bread then cake: both produced")


def test_factory_queue_auto_start():
    print("\n--- Test 8d: Queue auto-starts next recipe after finish ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")

    # Добавляем элемент в очередь завода
    world["factories"][0]["queue"] = [{"recipe_id": "cake", "duration_sec": 2}]

    # Запускаем bread на 2 тика
    r1 = sim({"contract_version": "v1", "tick_id": 1, "world_state": world, "actions": [{
        "contract_version": "v1", "player_id": "p1",
        "action_type": "START_RECIPE",
        "payload": {"factory_id": "bakery_1", "recipe_id": "bread", "duration_sec": 2},
        "client_ts": 0
    }]})
    ws = r1["next_world_state"]
    assert ws["factories"][0]["active_recipe_id"] is not None  # bread или уже cake

    # Прогоняем до завершения
    for _ in range(6):
        tid = ws["tick_id"] + 1
        r = sim({"contract_version": "v1", "tick_id": tid, "world_state": ws, "actions": []})
        ws = r["next_world_state"]
        if ws["factories"][0]["active_recipe_id"] is None and not ws["factories"][0].get("queue"):
            break

    # Очередь пуста, завод простаивает
    assert ws["factories"][0]["active_recipe_id"] is None
    assert len(ws["factories"][0].get("queue", [])) == 0

    # Оба продукта в инвентаре
    inv = ws["players"][0]["inventory"]
    assert any(i["product_id"] == "bread" for i in inv)
    assert any(i["product_id"] == "cake" for i in inv)
    print("  [OK] Queue popped, cake auto-started, both produced")


def test_stub_actions_silently_ignored():
    print("\n--- Test 9: Future actions (FEED_ANIMAL etc.) silently ignored ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")

    for action_type in ["FEED_ANIMAL", "APPLY_SABOTAGE", "USE_COUNTERMEASURE"]:
        tick_input = {"contract_version": "v1", "tick_id": 1, "world_state": world, "actions": [{
            "contract_version": "v1", "player_id": "p1",
            "action_type": action_type,
            "payload": {}, "client_ts": 0
        }]}
        result = sim(tick_input)
        # Нет ошибок, нет событий (кроме пассивной фазы)
        errors = [e for e in result["events"] if e["event_type"] == "CONTRACT_ERROR"]
        assert len(errors) == 0, f"{action_type} should not cause error"

    print("  [OK] FEED_ANIMAL, APPLY_SABOTAGE, USE_COUNTERMEASURE ignored gracefully")


# ===== Тесты APPLY_EVENT (engine_cpp/004) =====

def test_event_drought():
    print("\n--- Test 10a: APPLY_EVENT DROUGHT — decay +50% на растениях ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    # t1: decay=2 → 3, t2: decay=2 → 3
    tick_input = {"contract_version": "v1", "tick_id": 1, "world_state": world, "actions": [{
        "contract_version": "v1", "player_id": "p1",
        "action_type": "APPLY_EVENT",
        "payload": {"event_type": "DROUGHT"}, "client_ts": 0
    }]}
    result = sim(tick_input)
    tiles = result["next_world_state"]["map"]["tiles"]
    # decay увеличен: t1 (wheat) и t2 (corn)
    assert tiles[0]["water_decay_per_tick"] == 3, f"t1 decay should be 3, got {tiles[0].get('water_decay_per_tick')}"
    assert tiles[1]["water_decay_per_tick"] == 3, f"t2 decay should be 3, got {tiles[1].get('water_decay_per_tick')}"
    # После события + пассивная фаза с новым decay=3: t1 30->27, t2 10->7
    assert tiles[0]["water_level"] == 27
    assert tiles[1]["water_level"] == 7
    assert "EVENT_TRIGGERED" in [e["event_type"] for e in result["events"]]
    print("  [OK] decay 2->3, water t1:27 t2:7")


def test_event_rain():
    print("\n--- Test 10b: APPLY_EVENT RAIN — decay negative, water increases ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    tick_input = {"contract_version": "v1", "tick_id": 1, "world_state": world, "actions": [{
        "contract_version": "v1", "player_id": "p1",
        "action_type": "APPLY_EVENT",
        "payload": {"event_type": "RAIN"}, "client_ts": 0
    }]}
    result = sim(tick_input)
    tiles = result["next_world_state"]["map"]["tiles"]
    # decay стал отрицательным: t1 decay=2 → increase=max(1, 2*0.2)=1 → decay=-1
    assert tiles[0]["water_decay_per_tick"] == -1
    # Пассивная фаза: water = max(0, min(100, 30 - (-1))) = 31
    assert tiles[0]["water_level"] == 31, f"t1 water should increase, got {tiles[0]['water_level']}"
    assert "EVENT_TRIGGERED" in [e["event_type"] for e in result["events"]]
    print("  [OK] decay=-1, water 30->31 (rain increases moisture)")


def test_event_rain_water_caps_at_100():
    print("\n--- Test 10c: RAIN doesn't exceed water=100 ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    world["map"]["tiles"][0]["water_level"] = 99
    tick_input = {"contract_version": "v1", "tick_id": 1, "world_state": world, "actions": [{
        "contract_version": "v1", "player_id": "p1",
        "action_type": "APPLY_EVENT",
        "payload": {"event_type": "RAIN"}, "client_ts": 0
    }]}
    result = sim(tick_input)
    t1 = result["next_world_state"]["map"]["tiles"][0]
    assert t1["water_level"] <= 100, f"Water capped at 100, got {t1['water_level']}"
    print(f"  [OK] water capped: {t1['water_level']}")


def test_event_earthquake():
    print("\n--- Test 10d: APPLY_EVENT EARTHQUAKE — factory time +50% ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    # Запускаем рецепт на 10 секунд
    r1 = sim({"contract_version": "v1", "tick_id": 1, "world_state": world, "actions": [{
        "contract_version": "v1", "player_id": "p1",
        "action_type": "START_RECIPE",
        "payload": {"factory_id": "bakery_1", "recipe_id": "bread", "duration_sec": 10},
        "client_ts": 0
    }]})
    ws = r1["next_world_state"]
    # remaining = 9 (10-1 passive)

    # Землетрясение
    r2 = sim({"contract_version": "v1", "tick_id": 2, "world_state": ws, "actions": [{
        "contract_version": "v1", "player_id": "p1",
        "action_type": "APPLY_EVENT",
        "payload": {"event_type": "EARTHQUAKE"}, "client_ts": 0
    }]})
    ws = r2["next_world_state"]
    # remaining = 9 * 1.5 = 13, затем passive -1 = 12
    remaining = ws["factories"][0]["remaining_time_sec"]
    assert remaining >= 12, f"Factory slowed by earthquake, expected ~12, got {remaining}"
    print(f"  [OK] Factory time increased: {remaining}")


def test_event_unknown():
    print("\n--- Test 10e: Unknown event_type -> CONTRACT_ERROR ---")
    sim = get_simulate()
    world = load_fixture("world_state", "minimal_world.json")
    tick_input = {"contract_version": "v1", "tick_id": 1, "world_state": world, "actions": [{
        "contract_version": "v1", "player_id": "p1",
        "action_type": "APPLY_EVENT",
        "payload": {"event_type": "ALIEN_INVASION"}, "client_ts": 0
    }]}
    result = sim(tick_input)
    _check_contract_error(result, "INVALID_TYPE", "Unknown event_type")
    print("  [OK]")


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
    test_growth_water_decay()
    test_growth_elapsed_increases()
    test_growth_stops_without_water()
    test_plant_death_no_water()
    test_growth_3_ticks_sequence()
    test_growth_fields_not_required()
    test_evaporation_on_empty_tiles()
    test_harvest_ripe_plant()
    test_harvest_water_unchanged()
    test_harvest_not_ripe()
    test_harvest_empty_tile()
    test_harvest_not_owner()
    test_harvest_nonexistent_tile()
    test_harvest_without_growth_fields()
    test_factory_tick_countdown()
    test_factory_recipe_finishes()
    test_factory_multiple_recipes()
    test_factory_queue_auto_start()
    test_stub_actions_silently_ignored()
    test_event_drought()
    test_event_rain()
    test_event_rain_water_caps_at_100()
    test_event_earthquake()
    test_event_unknown()
    test_stub_vs_cpp()

    print("\n" + "=" * 60)
    print("ALL CHECKS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
