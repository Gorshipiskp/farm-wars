cmake_minimum_required(VERSION 3.15)
project(engine_core)

# Найти pybind11 (установлен через pip install pybind11)
find_package(pybind11 REQUIRED)

# Собрать Python-модуль с именем "engine_core"
pybind11_add_module(engine_core
    src/engine_core.cpp
    src/simulate_tick.cpp
)

# Подсказать компилятору, где искать наши заголовочные файлы
target_include_directories(engine_core PRIVATE src)
