/*
    Точка входа C++ модуля engine_core для Python.

    pybind11 автоматически находит этот файл при сборке через pybind11_add_module.
    Здесь мы говорим Python: "вот функция simulate_tick, вызывай ее из Python".
*/

#include <pybind11/pybind11.h>
#include "simulate_tick.h"

namespace py = pybind11;

/*
    PYBIND11_MODULE — макрос, который создает Python-модуль.
    Первый аргумент: имя модуля (engine_core — так его будут импортировать в Python).
    Второй аргумент: переменная m, через которую мы регистрируем функции и классы.
*/
PYBIND11_MODULE(engine_core, m) {
    m.doc() = "Farm Wars C++ simulation core (engine_core v1)";

    /*
        Регистрируем функцию simulate_tick.
        Первый аргумент: имя функции в Python (как ее вызывать).
        Второй аргумент: указатель на C++ функцию.
        Третий аргумент: описание (покажется в help()).
    */
    m.def("simulate_tick", &simulate_tick,
          "Обработать один тик симуляции.\n"
          "Принимает dict TickInput, возвращает dict TickResult.");
}
