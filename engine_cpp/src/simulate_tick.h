#pragma once

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

/*
    Функция simulate_tick — сердце C++ движка.
    Получает на вход текущее состояние мира + действия игроков,
    возвращает новое состояние мира + события, которые произошли.

    Сигнатура:
        input:  dict (TickInput из контракта v1)
        output: dict (TickResult из контракта v1)

    Сейчас это заглушка (stub): обрабатывает только WATER_PLANT и START_RECIPE,
    без реальной физики роста/болезней. Настоящая логика добавится в следующих задачах.
*/
py::dict simulate_tick(py::dict input);
