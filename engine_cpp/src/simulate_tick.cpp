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
                          const std::string& field_path = "") {
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
               const std::string& code, const std::string& msg, const std::string& path) {
    errors.append(make_error_event(tick_id, code, msg, path));
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


// ----- Поиск объектов в списках -----

py::dict find_tile(py::list tiles, const std::string& tile_id) {
    for (auto& item : tiles) {
        auto tile = item.cast<py::dict>();
        if (tile["tile_id"].cast<std::string>() == tile_id) {
            return tile;
        }
    }
    throw std::runtime_error("Tile not found: " + tile_id);
}

py::dict find_factory(py::list factories, const std::string& factory_id) {
    for (auto& item : factories) {
        auto factory = item.cast<py::dict>();
        if (factory["factory_id"].cast<std::string>() == factory_id) {
            return factory;
        }
    }
    throw std::runtime_error("Factory not found: " + factory_id);
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
            try {
                py::dict tile = find_tile(tiles, tile_id);
                tile["water_level"] = 100;

                py::dict ev_payload;
                ev_payload["tile_id"] = tile_id;
                ev_payload["player_id"] = player_id;
                events.append(make_game_event("PLANT_WATERED", tick_id, ev_payload));

            } catch (const std::runtime_error& e) {
                events.append(make_error_event(tick_id, "MISSING_FIELD", e.what()));
            }

        } else if (action_type == "START_RECIPE") {
            std::string factory_id = payload["factory_id"].cast<std::string>();
            std::string recipe_id = payload["recipe_id"].cast<std::string>();
            int duration_sec = payload["duration_sec"].cast<int>();
            try {
                py::dict factory = find_factory(factories, factory_id);
                factory["active_recipe_id"] = recipe_id;
                factory["remaining_time_sec"] = duration_sec;

                py::dict ev_payload;
                ev_payload["factory_id"] = factory_id;
                ev_payload["recipe_id"] = recipe_id;
                ev_payload["player_id"] = player_id;
                events.append(make_game_event("RECIPE_STARTED", tick_id, ev_payload));

            } catch (const std::runtime_error& e) {
                events.append(make_error_event(tick_id, "MISSING_FIELD", e.what()));
            }

        } else {
            events.append(make_error_event(
                tick_id, "INVALID_TYPE",
                "Unknown action_type: " + action_type));
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
