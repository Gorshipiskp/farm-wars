# Сборка C++ модуля engine_core через CMake + pybind11.
# Требования: Visual Studio 2022, Python 3.13, pybind11 (pip install pybind11).
#
# Запуск из корня проекта:
#   powershell -ExecutionPolicy Bypass -File tools/build_engine.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Building engine_core (C++ module) ===" -ForegroundColor Cyan

# Python: используем py launcher (он гарантированно выберет Python 3.13)
$pythonCmd = "py"

# Шаг 1: находим pybind11 CMake-файлы
$pybind11Dir = & $pythonCmd -c "import pybind11; print(pybind11.get_cmake_dir())"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: pybind11 not found. Run: py -m pip install pybind11" -ForegroundColor Red
    exit 1
}
Write-Host "pybind11 cmake dir: $pybind11Dir"

# Шаг 2: находим CMake из Visual Studio 2022
$cmakePath = "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
if (-not (Test-Path $cmakePath)) {
    # Пробуем Professional или Enterprise редакцию
    $cmakePath = (Get-ChildItem -Path "C:\Program Files\Microsoft Visual Studio\2022" -Recurse -Filter "cmake.exe" -ErrorAction SilentlyContinue | Select-Object -First 1).FullName
}
if (-not $cmakePath) {
    Write-Host "ERROR: CMake not found. Install Visual Studio 2022 with C++ tools." -ForegroundColor Red
    exit 1
}
Write-Host "CMake path: $cmakePath"

# Шаг 3: настраиваем среду Visual Studio (чтобы cl.exe был доступен)
$vsPath = "C:\Program Files\Microsoft Visual Studio\2022\Community"
$vcvarsPath = "$vsPath\VC\Auxiliary\Build\vcvars64.bat"
if (-not (Test-Path $vcvarsPath)) {
    Write-Host "ERROR: vcvars64.bat not found at $vcvarsPath" -ForegroundColor Red
    exit 1
}

Write-Host "Setting up MSVC environment..."
$envSetup = cmd /c "`"$vcvarsPath`" > nul 2>&1 && set"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: vcvars failed" -ForegroundColor Red
    exit 1
}

# Парсим вывод vcvars и применяем переменные окружения
$envSetup -split "`n" | ForEach-Object {
    if ($_ -match "^(.*?)=(.*)$") {
        $name = $matches[1]
        $value = $matches[2]
        Set-Item -Path "env:$name" -Value $value -ErrorAction SilentlyContinue
    }
}

# Шаг 4: конфигурируем CMake
Write-Host "Configuring CMake..."
& $cmakePath -B engine_cpp/build -S engine_cpp -Dpybind11_DIR="$pybind11Dir"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: CMake configure failed" -ForegroundColor Red
    exit 1
}

# Шаг 5: собираем
Write-Host "Building..."
& $cmakePath --build engine_cpp/build --config Release
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed" -ForegroundColor Red
    exit 1
}

Write-Host "=== Build successful! ===" -ForegroundColor Green

# Шаг 6: показываем, где лежит собранный модуль
$pydPath = Get-ChildItem -Path "engine_cpp\build\Release" -Filter "*.pyd" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pydPath) {
    Write-Host "Module: $($pydPath.FullName)"
} else {
    Write-Host "Module built (check engine_cpp/build/Release/)"
}
