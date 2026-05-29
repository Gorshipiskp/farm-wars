#include "simulate_tick.h"

#include <string>
#include <vector>


// ----- Вспомогательные функции для создания событий -----

/*
    Собирает dict для CONTRACT_ERROR события.
    Это стандартный формат ошибки из GAME_CONTRACTS_V1.md, секция 7.
*/
py::dict make_error_event(int tick_id,
                          const std::string& error_code,
                          const std::string& message,
                          const std::string& field_path = "",
                          const std::string& player_id = "") {
    py::dict event;
    event["contract_version"] = "v1";
    event["event_type"] = "CONTRACT_ERROR";
    event["server_tick"] = tick_id;

    py::dict payload;
    payload["error_code"] = error_code;
    payload["message"] = message;
    if (field_path.empty()) {
        payload["field_path"] = py::none();
    } else {
        payload["field_path"] = field_path;
    }
    if (player_id.empty()) {
        payload["player_id"] = py::none();
    } else {
        payload["player_id"] = player_id;
    }
    event["payload"] = payload;
    return event;
}

/*
    Собирает dict для обычного игрового события (PLANT_WATERED, RECIPE_STARTED, ...).
*/
py::dict make_game_event(const std::string& event_type,
                         int tick_id,
                         py::dict payload) {
    py::dict event;
    event["contract_version"] = "v1";
    event["event_type"] = event_type;
    event["server_tick"] = tick_id;
    event["payload"] = payload;
    return event;
}

// ----- Проверка наличия и типа полей -----

/*
    Проверяет, что поле с именем key ЕСТЬ в dict (даже если значение None).
*/
bool has_field(py::dict d, const std::string& key) {
    return d.contains(key);
}

// Удобный короткий псевдоним для добавления CONTRACT_ERROR в список
void add_error(py::list& errors, int tick_id,
               const std::string& code, const std::string& msg,
               const std::string& path, const std::string& player_id = "") {
    errors.append(make_error_event(tick_id, code, msg, path, player_id));
}

/*
    Проверяет наличие и тип поля. Если что-то не так — добавляет ошибку в errors.
    Возвращает true если поле прошло проверку, false если есть ошибка.
*/
bool check_field(py::dict d, const char* key,
                 const std::string& expected_py_type,
                 const std::string& path,
                 int tick_id,
                 py::list& errors) {

    // Проверка наличия
    if (!has_field(d, key)) {
        std::string msg = "MISSING_FIELD: " + path + "." + key;
        add_error(errors, tick_id, "MISSING_FIELD", msg, path + "." + key);
        return false;
    }

    // Проверка типа
    auto val = d[key];
    bool type_ok = false;

    if (expected_py_type == "str") {
        type_ok = py::isinstance<py::str>(val);
    } else if (expected_py_type == "int") {
        type_ok = py::isinstance<py::int_>(val) || py::isinstance<py::float_>(val);
    } else if (expected_py_type == "dict") {
        type_ok = py::isinstance<py::dict>(val);
    } else if (expected_py_type == "list") {
        type_ok = py::isinstance<py::list>(val);
    }

    if (!type_ok) {
        std::string type_label;
        if (expected_py_type == "str") type_label = "string";
        else if (expected_py_type == "int") type_label = "number";
        else if (expected_py_type == "dict") type_label = "object";
        else if (expected_py_type == "list") type_label = "array";
        else type_label = expected_py_type;

        std::string msg = "INVALID_TYPE: " + path + "." + key + " (expected " + type_label + ")";
        add_error(errors, tick_id, "INVALID_TYPE", msg, path + "." + key);
        return false;
    }

    return true;
}


// ----- Валидация входных данных -----

/*
    validate_tick_input проверяет структуру TickInput на соответствие контракту v1.
    Возвращает список событий CONTRACT_ERROR (пустой список = все ok).
*/
py::list validate_tick_input(py::dict input) {
    py::list errors;

    // Безопасно определяем tick_id
    int tick_id = 0;
    if (has_field(input, "tick_id")) {
        auto tid_val = input["tick_id"];
        if (py::isinstance<py::int_>(tid_val)) {
            tick_id = tid_val.cast<int>();
        } else if (py::isinstance<py::float_>(tid_val)) {
            tick_id = static_cast<int>(tid_val.cast<double>());
        }
    }

    // --- Верхний уровень TickInput ---
    // contract_version: обязательно, должен быть "v1"
    if (check_field(input, "contract_version", "str", "tick_input", tick_id, errors)) {
        std::string ver = input["contract_version"].cast<std::string>();
        if (ver != "v1") {
            add_error(errors, tick_id, "UNSUPPORTED_VERSION",
                      "Expected v1, got: " + ver, "contract_version");
        }
    }

    // tick_id
    bool tid_ok = check_field(input, "tick_id", "int", "tick_input", tick_id, errors);
    if (tid_ok) {
        auto tid_val = input["tick_id"];
        if (py::isinstance<py::int_>(tid_val)) {
            tick_id = tid_val.cast<int>();
        } else {
            tick_id = static_cast<int>(tid_val.cast<double>());
        }
    }

    // world_state
    bool has_ws = check_field(input, "world_state", "dict", "tick_input", tick_id, errors);
    // actions
    bool has_acts = check_field(input, "actions", "list", "tick_input", tick_id, errors);

    if (!has_ws) return errors;

    // --- world_state ---
    py::dict ws = input["world_state"].cast<py::dict>();
    check_field(ws, "contract_version", "str", "world_state", tick_id, errors);
    check_field(ws, "match_id", "str", "world_state", tick_id, errors);
    check_field(ws, "tick_id", "int", "world_state", tick_id, errors);
    check_field(ws, "players", "list", "world_state", tick_id, errors);

    bool has_map = check_field(ws, "map", "dict", "world_state", tick_id, errors);
    if (has_map) {
        py::dict map = ws["map"].cast<py::dict>();
        check_field(map, "width", "int", "world_state.map", tick_id, errors);
        check_field(map, "height", "int", "world_state.map", tick_id, errors);
        check_field(map, "tiles", "list", "world_state.map", tick_id, errors);
    }

    check_field(ws, "factories", "list", "world_state", tick_id, errors);
    check_field(ws, "win_condition", "dict", "world_state", tick_id, errors);

    // --- actions ---
    if (!has_acts) return errors;

    py::list actions = input["actions"].cast<py::list>();
    for (size_t i = 0; i < actions.size(); i++) {
        if (!py::isinstance<py::dict>(actions[i])) {
            add_error(errors, tick_id, "INVALID_TYPE",
                      "actions[" + std::to_string(i) + "] is not an object",
                      "actions[" + std::to_string(i) + "]");
            continue;
        }

        auto action = actions[i].cast<py::dict>();
        std::string prefix = "actions[" + std::to_string(i) + "]";

        check_field(action, "contract_version", "str", prefix, tick_id, errors);
        check_field(action, "player_id", "str", prefix, tick_id, errors);
        check_field(action, "action_type", "str", prefix, tick_id, errors);
        check_field(action, "payload", "dict", prefix, tick_id, errors);
        check_field(action, "client_ts", "int", prefix, tick_id, errors);
    }

    return errors;
}


// ----- Поиск объектов в списках (индексы для гарантии in-place мутаций) -----

int find_tile_index(py::list tiles, const std::string& tile_id) {
    for (size_t i = 0; i < tiles.size(); i++) {
        auto tile = tiles[i].cast<py::dict>();
        if (tile["tile_id"].cast<std::string>() == tile_id) {
            return static_cast<int>(i);
        }
    }
    return -1;
}

int find_factory_index(py::list factories, const std::string& factory_id) {
    for (size_t i = 0; i < factories.size(); i++) {
        auto factory = factories[i].cast<py::dict>();
        if (factory["factory_id"].cast<std::string>() == factory_id) {
            return static_cast<int>(i);
        }
    }
    return -1;
}


// ----- Основная функция симуляции -----

py::dict simulate_tick(py::dict input) {
    // Безопасно определяем tick_id (может быть строка — тогда останется 0)
    int tick_id = 0;
    if (has_field(input, "tick_id")) {
        auto tid_val = input["tick_id"];
        if (py::isinstance<py::int_>(tid_val)) {
            tick_id = tid_val.cast<int>();
        } else if (py::isinstance<py::float_>(tid_val)) {
            tick_id = static_cast<int>(tid_val.cast<double>());
        }
    }

    // Шаг 1: валидация контракта
    py::list validation_errors = validate_tick_input(input);
    if (validation_errors.size() > 0) {
        // Если есть ошибки валидации — возвращаем неизмененное состояние + ошибки.
        // Игровой движок не должен обрабатывать некорректные данные.
        py::dict empty_state;
        empty_state["contract_version"] = "v1";
        empty_state["match_id"] = "error";
        empty_state["tick_id"] = tick_id;
        empty_state["players"] = py::list();
        empty_state["map"] = py::dict();
        empty_state["factories"] = py::list();
        empty_state["win_condition"] = py::dict();

        py::dict result;
        result["contract_version"] = "v1";
        result["tick_id"] = tick_id;
        result["next_world_state"] = empty_state;
        result["events"] = validation_errors;
        return result;
    }

    // Шаг 2: извлекаем проверенные данные
    py::dict world_state = input["world_state"].cast<py::dict>();
    py::list actions = input["actions"].cast<py::list>();

    // Шаг 3: глубокая копия состояния (чтобы не испортить оригинал)
    py::module_ copy_mod = py::module_::import("copy");
    py::dict next_world_state = copy_mod.attr("deepcopy")(world_state).cast<py::dict>();
    next_world_state["tick_id"] = tick_id;

    // Шаг 4: список событий
    py::list events;

    // Внутренние ссылки
    py::dict map_state = next_world_state["map"].cast<py::dict>();
    py::list tiles = map_state["tiles"].cast<py::list>();
    py::list factories = next_world_state["factories"].cast<py::list>();

    // Шаг 5: обработка действий
    for (auto& action_item : actions) {
        auto action = action_item.cast<py::dict>();
        std::string action_type = action["action_type"].cast<std::string>();
        std::string player_id = action["player_id"].cast<std::string>();
        py::dict payload = action["payload"].cast<py::dict>();

        if (action_type == "WATER_PLANT") {
            std::string tile_id = payload["tile_id"].cast<std::string>();
            int t_idx = find_tile_index(tiles, tile_id);
            if (t_idx < 0) {
                events.append(make_error_event(tick_id, "MISSING_FIELD",
                    "Tile not found: " + tile_id, "", player_id));
            } else {
                py::dict tile = tiles[t_idx].cast<py::dict>();
                std::string owner = tile["owner_player_id"].cast<std::string>();
                if (owner != player_id) {
                    events.append(make_error_event(
                        tick_id, "INVALID_TYPE",
                        "Tile not owned by " + player_id, "", player_id));
                } else {
                    tile["water_level"] = 100;

                    py::dict ev_payload;
                    ev_payload["tile_id"] = tile_id;
                    ev_payload["player_id"] = player_id;
                    events.append(make_game_event("PLANT_WATERED", tick_id, ev_payload));
                }
            }

        } else if (action_type == "START_RECIPE") {
            std::string factory_id = payload["factory_id"].cast<std::string>();
            std::string recipe_id = payload["recipe_id"].cast<std::string>();
            int duration_sec = payload["duration_sec"].cast<int>();
            int f_idx = find_factory_index(factories, factory_id);
            if (f_idx < 0) {
                events.append(make_error_event(tick_id, "MISSING_FIELD",
                    "Factory not found: " + factory_id, "", player_id));
            } else {
                py::dict factory = factories[f_idx].cast<py::dict>();

                // Проверка владельца завода
                bool owner_ok = true;
                if (factory.contains("owner_player_id")) {
                    std::string fowner = factory["owner_player_id"].cast<std::string>();
                    if (fowner != player_id) {
                        py::dict p;
                        p["player_id"] = player_id;
                        p["factory_id"] = factory_id;
                        p["recipe_id"] = recipe_id;
                        p["reason"] = "NOT_OWNER";
                        events.append(make_game_event("RECIPE_REJECTED", tick_id, p));
                        owner_ok = false;
                    }
                }

                if (owner_ok) {
                    factory["active_recipe_id"] = recipe_id;
                    factory["remaining_time_sec"] = duration_sec;
                    if (payload.contains("output_product_id")) {
                        factory["output_product_id"] = payload["output_product_id"];
                    }

                    py::dict ev_payload;
                    ev_payload["factory_id"] = factory_id;
                    ev_payload["recipe_id"] = recipe_id;
                    ev_payload["player_id"] = player_id;
                    events.append(make_game_event("RECIPE_STARTED", tick_id, ev_payload));
                }
            }

        } else if (action_type == "PLACE_ON_TILE") {
            std::string tile_id = payload["tile_id"].cast<std::string>();
            std::string plant_id = payload["plant_id"].cast<std::string>();
            std::string seed_product_id = plant_id;
            if (payload.contains("seed_product_id") && !payload["seed_product_id"].is_none()) {
                seed_product_id = payload["seed_product_id"].cast<std::string>();
            }
            int initial_health = payload["initial_health"].cast<int>();
            int initial_water = payload["initial_water_level"].cast<int>();

            int t_idx = find_tile_index(tiles, tile_id);
            if (t_idx < 0) {
                events.append(make_error_event(tick_id, "MISSING_FIELD",
                    "Tile not found: " + tile_id, "", player_id));
            } else {
                py::dict tile = tiles[t_idx].cast<py::dict>();

                // Проверить, что клетка принадлежит игроку
                std::string owner = tile["owner_player_id"].cast<std::string>();
                if (owner != player_id) {
                    events.append(make_error_event(tick_id, "INVALID_TYPE",
                        "Tile " + tile_id + " not owned by " + player_id, "", player_id));
                }
                // Проверить, что клетка пустая
                else if (!tile["occupant_type"].is_none() &&
                         tile["occupant_type"].cast<std::string>() != "EMPTY") {
                    events.append(make_error_event(tick_id, "INVALID_TYPE",
                        "Tile already occupied: " + tile_id, "", player_id));
                }
                // Проверить, что зона PLANT
                else if (tile["zone_type"].cast<std::string>() != "PLANT") {
                    std::string zone = tile["zone_type"].cast<std::string>();
                    events.append(make_error_event(tick_id, "INVALID_TYPE",
                        "Tile zone is " + zone + ", expected PLANT", "", player_id));
                }
                // Проверить инвентарь и списать семечко
                else {
                    // Найти игрока в world_state.players
                    py::list players_list = next_world_state["players"].cast<py::list>();
                    bool player_found = false;
                    bool inv_found = false;

                    for (auto& p_item : players_list) {
                        auto p = p_item.cast<py::dict>();
                        if (p["player_id"].cast<std::string>() != player_id) continue;
                        player_found = true;

                        // Проверить инвентарь игрока
                        py::list inventory = p["inventory"].cast<py::list>();
                        for (size_t inv_idx = 0; inv_idx < inventory.size(); inv_idx++) {
                            auto inv_item = inventory[inv_idx].cast<py::dict>();
                            if (inv_item["product_id"].cast<std::string>() != seed_product_id) continue;

                            int amount = inv_item["amount"].cast<int>();
                            if (amount < 1) {
                                events.append(make_error_event(tick_id, "MISSING_FIELD",
                                    "No " + seed_product_id + " in inventory for player " + player_id, "", player_id));
                                inv_found = true;
                                break;
                            }

                            // Списать 1 единицу
                            if (amount == 1) {
                                // Удаляем позицию — создаем новый список без нее
                                py::list new_inv;
                                for (size_t j = 0; j < inventory.size(); j++) {
                                    if (j != inv_idx) new_inv.append(inventory[j]);
                                }
                                p["inventory"] = new_inv;
                            } else {
                                inv_item["amount"] = amount - 1;
                            }

                            // Посадить растение на клетку (урожай — crop id)
                            tile["occupant_type"] = "PLANT";
                            std::string crop_id = plant_id;
                            if (payload.contains("crop_product_id") && !payload["crop_product_id"].is_none()) {
                                crop_id = payload["crop_product_id"].cast<std::string>();
                            }
                            tile["occupant_id"] = crop_id;
                            tile["health"] = initial_health;
                            if (payload.contains("initial_water_level")) {
                                int w = payload["initial_water_level"].cast<int>();
                                tile["water_level"] = std::max(0, std::min(100, w));
                            }

                            // Поля роста (опциональные — придут от сервера когда server/003 готов)
                            tile["growth_elapsed_sec"] = 0;
                            if (payload.contains("growth_time_sec")) {
                                tile["growth_time_sec"] = payload["growth_time_sec"];
                            }
                            if (payload.contains("water_decay_per_tick")) {
                                tile["water_decay_per_tick"] = payload["water_decay_per_tick"];
                            }

                            py::dict ev_payload;
                            ev_payload["tile_id"] = tile_id;
                            ev_payload["plant_id"] = plant_id;
                            ev_payload["player_id"] = player_id;
                            events.append(make_game_event("PLANT_PLACED", tick_id, ev_payload));

                            inv_found = true;
                            break;
                        }
                        break;
                    }

                    if (!player_found) {
                        events.append(make_error_event(tick_id, "MISSING_FIELD",
                            "Player not found: " + player_id, "", player_id));
                    } else if (!inv_found) {
                        events.append(make_error_event(tick_id, "MISSING_FIELD",
                            "No " + seed_product_id + " in inventory for player " + player_id, "", player_id));
                    }
                }
            }

        } else if (action_type == "BUY_PRODUCT") {
            // Server-only — ignore if leaked into engine.

        } else if (action_type == "BUY_ANIMAL" || action_type == "APPLY_SABOTAGE") {
            // Server-only — ignore if leaked into engine.

        } else if (action_type == "FEED_ANIMAL") {
            std::string tile_id = payload["tile_id"].cast<std::string>();
            int t_idx = find_tile_index(tiles, tile_id);
            if (t_idx < 0) {
                py::dict p;
                p["player_id"] = player_id;
                p["tile_id"] = tile_id;
                p["reason"] = "UNKNOWN_TILE";
                events.append(make_game_event("FEED_FAILED", tick_id, p));
            } else {
                py::dict tile = tiles[t_idx].cast<py::dict>();
                std::string owner = tile["owner_player_id"].cast<std::string>();
                if (owner != player_id) {
                    py::dict p;
                    p["player_id"] = player_id;
                    p["tile_id"] = tile_id;
                    p["reason"] = "NOT_OWNER";
                    events.append(make_game_event("FEED_FAILED", tick_id, p));
                } else if (tile["occupant_type"].is_none() ||
                           tile["occupant_type"].cast<std::string>() != "ANIMAL") {
                    py::dict p;
                    p["player_id"] = player_id;
                    p["tile_id"] = tile_id;
                    p["reason"] = "NO_ANIMAL";
                    events.append(make_game_event("FEED_FAILED", tick_id, p));
                } else {
                    if (payload.contains("production_interval_sec")) {
                        tile["production_interval_sec"] = payload["production_interval_sec"];
                    }
                    if (payload.contains("product_id")) {
                        tile["product_id"] = payload["product_id"];
                    }
                    tile["hunger_ticks"] = 0;
                    py::dict ev_payload;
                    ev_payload["player_id"] = player_id;
                    ev_payload["tile_id"] = tile_id;
                    if (tile.contains("occupant_id") && !tile["occupant_id"].is_none()) {
                        ev_payload["animal_id"] = tile["occupant_id"];
                    }
                    events.append(make_game_event("ANIMAL_FED", tick_id, ev_payload));
                }
            }

        } else if (action_type == "APPLY_SABOTAGE" || action_type == "USE_COUNTERMEASURE") {
            // Not implemented yet

        } else if (action_type == "APPLY_EVENT") {
            std::string event_type = payload["event_type"].cast<std::string>();
            int affected = 0;

            if (event_type == "DROUGHT") {
                // Засуха: скорость высыхания +50% на всех грядках с растениями
                for (auto& t_item : tiles) {
                    auto t = t_item.cast<py::dict>();
                    auto occ = t["occupant_type"];
                    if (occ.is_none()) continue;
                    if (occ.cast<std::string>() != "PLANT") continue;
                    int decay = 2;  // default если поле отсутствует
                    if (t.contains("water_decay_per_tick") && !t["water_decay_per_tick"].is_none()) {
                        decay = t["water_decay_per_tick"].cast<int>();
                    }
                    decay = std::max(1, static_cast<int>(decay * 1.5));
                    t["water_decay_per_tick"] = decay;
                    affected++;
                }
            } else if (event_type == "RAIN" || event_type == "FLOOD") {
                // Дождь: влажность растет со скоростью 0.2 от обычной убыли
                for (auto& t_item : tiles) {
                    auto t = t_item.cast<py::dict>();
                    if (!t.contains("water_level") || t["water_level"].is_none()) continue;
                    int decay = 1;  // default evaporation
                    if (t.contains("water_decay_per_tick") && !t["water_decay_per_tick"].is_none()) {
                        decay = t["water_decay_per_tick"].cast<int>();
                        if (decay < 0) decay = 1;  // если уже идет дождь
                    }
                    int increase = std::max(1, static_cast<int>(decay * 0.2));
                    t["water_decay_per_tick"] = -increase;  // отрицательный = влажность растет
                    affected++;
                }
            } else if (event_type == "EARTHQUAKE") {
                // Землетрясение: скорость заводов -50% (remaining_time умножается на 1.5)
                py::list all_factories = next_world_state["factories"].cast<py::list>();
                for (auto& f_item : all_factories) {
                    auto f = f_item.cast<py::dict>();
                    if (f["active_recipe_id"].is_none()) continue;
                    int remaining = f["remaining_time_sec"].cast<int>();
                    if (remaining <= 0) continue;
                    remaining = static_cast<int>(remaining * 1.5);
                    f["remaining_time_sec"] = remaining;
                    affected++;
                }
            } else if (event_type == "EPIDEMIC") {
                for (auto& t_item : tiles) {
                    auto t = t_item.cast<py::dict>();
                    auto occ = t["occupant_type"];
                    if (occ.is_none()) continue;
                    if (occ.cast<std::string>() != "ANIMAL") continue;
                    int interval = 12;
                    if (t.contains("production_interval_sec") &&
                        !t["production_interval_sec"].is_none()) {
                        interval = t["production_interval_sec"].cast<int>();
                    }
                    t["production_interval_sec"] = static_cast<int>(interval * 1.5);
                    affected++;
                }
            } else {
                events.append(make_error_event(tick_id, "INVALID_TYPE",
                    "Unknown event_type: " + event_type, "", player_id));
            }

            if (affected > 0 || event_type == "DROUGHT" || event_type == "RAIN" ||
                event_type == "FLOOD" || event_type == "EARTHQUAKE" || event_type == "EPIDEMIC") {
                py::dict ev_payload;
                ev_payload["event_type"] = event_type;
                ev_payload["severity"] = 1.0;
                ev_payload["affected_tiles"] = affected;
                events.append(make_game_event("EVENT_TRIGGERED", tick_id, ev_payload));
            }

        } else if (action_type == "HARVEST_PLANT") {
            std::string tile_id = payload["tile_id"].cast<std::string>();
            bool harvest_handled = false;

            int t_idx = find_tile_index(tiles, tile_id);
            if (t_idx < 0) {
                py::dict p;
                p["player_id"] = player_id; p["tile_id"] = tile_id; p["reason"] = "UNKNOWN_TILE";
                events.append(make_game_event("HARVEST_FAILED", tick_id, p));
            } else {
                py::dict tile = tiles[t_idx].cast<py::dict>();

                // Проверить владельца
                std::string owner = tile["owner_player_id"].cast<std::string>();
                if (owner != player_id) {
                    py::dict p;
                    p["player_id"] = player_id; p["tile_id"] = tile_id; p["reason"] = "NOT_OWNER";
                    events.append(make_game_event("HARVEST_FAILED", tick_id, p));
                    harvest_handled = true;
                }
                // Проверить что есть растение
                else if (tile["occupant_type"].is_none() ||
                         tile["occupant_type"].cast<std::string>() != "PLANT") {
                    py::dict p;
                    p["player_id"] = player_id; p["tile_id"] = tile_id; p["reason"] = "NO_PLANT";
                    events.append(make_game_event("HARVEST_FAILED", tick_id, p));
                    harvest_handled = true;
                }
                // Проверить зрелость (если есть growth поля)
                else if (tile.contains("growth_time_sec") && !tile["growth_time_sec"].is_none() &&
                         tile.contains("growth_elapsed_sec") && !tile["growth_elapsed_sec"].is_none()) {
                    int elapsed = tile["growth_elapsed_sec"].cast<int>();
                    int needed = tile["growth_time_sec"].cast<int>();
                    if (elapsed < needed) {
                        py::dict p;
                        p["player_id"] = player_id; p["tile_id"] = tile_id; p["reason"] = "NOT_RIPE";
                        events.append(make_game_event("HARVEST_FAILED", tick_id, p));
                        harvest_handled = true;
                    }
                }
                if (!harvest_handled && tile.contains("water_level") && !tile["water_level"].is_none()) {
                    int water = tile["water_level"].cast<int>();
                    if (water < 50) {
                        py::dict p;
                        p["player_id"] = player_id; p["tile_id"] = tile_id; p["reason"] = "NOT_READY";
                        events.append(make_game_event("HARVEST_FAILED", tick_id, p));
                        harvest_handled = true;
                    }
                }

                if (!harvest_handled) {
                    // Успех: добавить продукт в инвентарь
                    std::string product_id = "";
                    if (tile.contains("occupant_id") && !tile["occupant_id"].is_none()) {
                        product_id = tile["occupant_id"].cast<std::string>();
                    }
                    const int HARVEST_YIELD = 2;

                    py::list plist = next_world_state["players"].cast<py::list>();
                    for (auto& p_item : plist) {
                        auto p = p_item.cast<py::dict>();
                        if (p["player_id"].cast<std::string>() != player_id) continue;

                        py::list inv = p["inventory"].cast<py::list>();
                        bool found = false;
                        for (auto& inv_item : inv) {
                            auto item = inv_item.cast<py::dict>();
                            if (item["product_id"].cast<std::string>() == product_id) {
                                int amt = item["amount"].cast<int>();
                                item["amount"] = amt + HARVEST_YIELD;
                                found = true;
                                break;
                            }
                        }
                        if (!found) {
                            py::dict new_item;
                            new_item["product_id"] = product_id;
                            new_item["amount"] = HARVEST_YIELD;
                            inv.append(new_item);
                        }
                        break;
                    }

                    // Очистить растение (влажность грядки остается)
                    tile["occupant_type"] = "EMPTY";
                    tile["occupant_id"] = py::none();
                    tile["health"] = py::none();
                    tile["growth_elapsed_sec"] = py::none();
                    tile["growth_time_sec"] = py::none();
                    tile["water_decay_per_tick"] = py::none();

                    py::dict ev_payload;
                    ev_payload["player_id"] = player_id;
                    ev_payload["tile_id"] = tile_id;
                    ev_payload["product_id"] = product_id;
                    ev_payload["amount"] = HARVEST_YIELD;
                    events.append(make_game_event("PLANT_HARVESTED", tick_id, ev_payload));
                }
            }
        } else {
            events.append(make_error_event(
                tick_id, "INVALID_TYPE",
                "Unknown action_type: " + action_type));
        }
    }

    // Шаг 5.5: пассивная фаза — испарение воды со всех грядок, рост/смерть растений
    {
        const int HEALTH_DECAY_PER_TICK = 10;
        const int DEFAULT_EVAPORATION = 0;  // пустые грядки без испарения (урожай — water_decay из БД)

        py::dict map = next_world_state["map"].cast<py::dict>();
        py::list all_tiles = map["tiles"].cast<py::list>();

        for (auto& t_item : all_tiles) {
            auto tile = t_item.cast<py::dict>();

            // --- Испарение воды (для всех грядок) ---
            if (tile.contains("water_level") && !tile["water_level"].is_none()) {
                int water = tile["water_level"].cast<int>();
                if (water > 0) {
                    int decay = DEFAULT_EVAPORATION;
                    if (tile.contains("water_decay_per_tick") && !tile["water_decay_per_tick"].is_none()) {
                        decay = tile["water_decay_per_tick"].cast<int>();
                    }
                    water = std::min(100, std::max(0, water - decay));
                    tile["water_level"] = water;
                }
            }

            // --- Дальше только растения ---
            auto occ_type = tile["occupant_type"];
            if (occ_type.is_none()) continue;
            if (occ_type.cast<std::string>() != "PLANT") continue;

            int water = 0;
            if (tile.contains("water_level") && !tile["water_level"].is_none()) {
                water = tile["water_level"].cast<int>();
            }

            // Рост (если есть вода)
            if (water > 0) {
                int elapsed = 0;
                if (tile.contains("growth_elapsed_sec") && !tile["growth_elapsed_sec"].is_none()) {
                    elapsed = tile["growth_elapsed_sec"].cast<int>();
                }
                tile["growth_elapsed_sec"] = elapsed + 1;
                continue;
            }

            // Без воды: потеря здоровья
            int health = 100;
            if (tile.contains("health") && !tile["health"].is_none()) {
                health = tile["health"].cast<int>();
            }
            health -= HEALTH_DECAY_PER_TICK;

            if (health <= 0) {
                std::string dead_plant = "";
                if (tile.contains("occupant_id") && !tile["occupant_id"].is_none()) {
                    dead_plant = tile["occupant_id"].cast<std::string>();
                }
                std::string dead_tile = "";
                if (tile.contains("tile_id")) {
                    dead_tile = tile["tile_id"].cast<std::string>();
                }
                std::string owner = "";
                if (tile.contains("owner_player_id")) {
                    owner = tile["owner_player_id"].cast<std::string>();
                }

                tile["occupant_type"] = "EMPTY";
                tile["occupant_id"] = py::none();
                tile["health"] = py::none();
                // water_level остается — влажность грядки
                tile["growth_elapsed_sec"] = py::none();
                tile["growth_time_sec"] = py::none();
                tile["water_decay_per_tick"] = py::none();

                py::dict ev_payload;
                ev_payload["tile_id"] = dead_tile;
                ev_payload["plant_id"] = dead_plant;
                ev_payload["player_id"] = owner;
                ev_payload["reason"] = "DEHYDRATED";
                events.append(make_game_event("PLANT_DIED", tick_id, ev_payload));
            } else {
                tile["health"] = health;
            }
        }
    }

    // Шаг 5.55: пассивная фаза животных
    {
        const int ANIMAL_HUNGER_LIMIT = 400;
        py::list all_players = next_world_state["players"].cast<py::list>();
        py::dict map = next_world_state["map"].cast<py::dict>();
        py::list all_tiles = map["tiles"].cast<py::list>();

        for (auto& t_item : all_tiles) {
            auto tile = t_item.cast<py::dict>();
            auto occ = tile["occupant_type"];
            if (occ.is_none()) continue;
            if (occ.cast<std::string>() != "ANIMAL") continue;
            if (tile["occupant_id"].is_none()) continue;

            int hunger = 0;
            if (tile.contains("hunger_ticks") && !tile["hunger_ticks"].is_none()) {
                hunger = tile["hunger_ticks"].cast<int>();
            }
            hunger += 1;
            tile["hunger_ticks"] = hunger;
            if (hunger > ANIMAL_HUNGER_LIMIT) continue;

            int interval = 12;
            if (tile.contains("production_interval_sec") &&
                !tile["production_interval_sec"].is_none()) {
                interval = tile["production_interval_sec"].cast<int>();
            }
            int elapsed = 0;
            if (tile.contains("production_elapsed_sec") &&
                !tile["production_elapsed_sec"].is_none()) {
                elapsed = tile["production_elapsed_sec"].cast<int>();
            }
            elapsed += 1;
            tile["production_elapsed_sec"] = elapsed;
            if (elapsed < interval) continue;

            tile["production_elapsed_sec"] = 0;
            std::string product_id = "milk";
            if (tile.contains("product_id") && !tile["product_id"].is_none()) {
                product_id = tile["product_id"].cast<std::string>();
            }
            std::string owner_id = tile["owner_player_id"].cast<std::string>();

            for (auto& p_item : all_players) {
                auto p = p_item.cast<py::dict>();
                if (p["player_id"].cast<std::string>() != owner_id) continue;

                py::list inv = p["inventory"].cast<py::list>();
                bool found = false;
                for (auto& inv_item : inv) {
                    auto item = inv_item.cast<py::dict>();
                    if (item["product_id"].cast<std::string>() == product_id) {
                        int amt = item["amount"].cast<int>();
                        item["amount"] = amt + 1;
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    py::dict new_item;
                    new_item["product_id"] = product_id;
                    new_item["amount"] = 1;
                    inv.append(new_item);
                }
                break;
            }

            py::dict ev_payload;
            ev_payload["player_id"] = owner_id;
            if (tile.contains("tile_id")) {
                ev_payload["tile_id"] = tile["tile_id"];
            }
            ev_payload["product_id"] = product_id;
            ev_payload["amount"] = 1;
            events.append(make_game_event("ANIMAL_PRODUCED", tick_id, ev_payload));
        }
    }

    // Шаг 5.6: пассивная фаза заводов — таймер рецепта
    {
        py::list all_factories = next_world_state["factories"].cast<py::list>();
        py::list all_players = next_world_state["players"].cast<py::list>();

        for (auto& f_item : all_factories) {
            auto factory = f_item.cast<py::dict>();

            // Только активные заводы с таймером > 0
            if (factory["active_recipe_id"].is_none()) continue;
            int remaining = factory["remaining_time_sec"].cast<int>();
            if (remaining <= 0) continue;

            remaining -= 1;
            factory["remaining_time_sec"] = remaining;

            if (remaining > 0) continue;

            // Рецепт завершен
            std::string recipe_id = factory["active_recipe_id"].cast<std::string>();
            std::string owner_id = factory["owner_player_id"].cast<std::string>();
            std::string factory_id = factory["factory_id"].cast<std::string>();
            std::string product_id = recipe_id;
            if (factory.contains("output_product_id") && !factory["output_product_id"].is_none()) {
                product_id = factory["output_product_id"].cast<std::string>();
            }

            // Найти владельца и добавить продукт в инвентарь
            for (auto& p_item : all_players) {
                auto p = p_item.cast<py::dict>();
                if (p["player_id"].cast<std::string>() != owner_id) continue;

                py::list inv = p["inventory"].cast<py::list>();
                bool found = false;
                for (auto& inv_item : inv) {
                    auto item = inv_item.cast<py::dict>();
                    if (item["product_id"].cast<std::string>() == product_id) {
                        item["amount"] = item["amount"].cast<int>() + 1;
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    py::dict new_item;
                    new_item["product_id"] = product_id;
                    new_item["amount"] = 1;
                    inv.append(new_item);
                }
                break;
            }

            factory["active_recipe_id"] = py::none();
            if (factory.contains("output_product_id")) {
                factory["output_product_id"] = py::none();
            }

            py::dict ev_payload;
            ev_payload["factory_id"] = factory_id;
            ev_payload["recipe_id"] = recipe_id;
            ev_payload["product_id"] = product_id;
            ev_payload["player_id"] = owner_id;
            events.append(make_game_event("RECIPE_FINISHED", tick_id, ev_payload));

            // Авто-запуск следующего рецепта из очереди
            if (factory.contains("queue")) {
                py::list queue = factory["queue"].cast<py::list>();
                if (queue.size() > 0) {
                    py::dict next_job = queue[py::int_(0)].cast<py::dict>();
                    std::string next_recipe = next_job["recipe_id"].cast<std::string>();

                    // Удалить первый элемент из очереди
                    py::list new_queue;
                    for (size_t qi = 1; qi < queue.size(); qi++) {
                        new_queue.append(queue[qi]);
                    }
                    factory["queue"] = new_queue;

                    // Запустить рецепт (длительность из queue item или по умолчанию 30)
                    int duration = 30;
                    if (next_job.contains("duration_sec") && !next_job["duration_sec"].is_none()) {
                        duration = next_job["duration_sec"].cast<int>();
                    }
                    factory["active_recipe_id"] = next_recipe;
                    factory["remaining_time_sec"] = duration;

                    py::dict q_payload;
                    q_payload["factory_id"] = factory_id;
                    q_payload["recipe_id"] = next_recipe;
                    q_payload["player_id"] = owner_id;
                    events.append(make_game_event("RECIPE_STARTED", tick_id, q_payload));
                }
            }
        }
    }

    // Шаг 6: собираем TickResult
    py::dict result;
    result["contract_version"] = "v1";
    result["tick_id"] = tick_id;
    result["next_world_state"] = next_world_state;
    result["events"] = events;

    return result;
}
