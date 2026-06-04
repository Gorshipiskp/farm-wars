# Farm Wars — установка и запуск (релиз)

## Вариант 1: готовая сборка (рекомендуется)

На машине **с Windows**, где собирали релиз:

```bash
bash build-release.sh
```

Результат: папка [`release/out/dist/FarmWars/`](release/out/dist/FarmWars/)

| Файл | Действие |
|------|----------|
| `Play-FarmWars.bat` | двойной клик — игра |
| `Play-FarmWars.sh` | то же из Git Bash |
| `FarmWars.exe` | только сервер + UI в браузере |

Скопируйте **всю папку `FarmWars`** на другой ПК — Python и Node не нужны.

- Игра откроется в браузере: `http://127.0.0.1:8765/`
- Друзья в LAN: `http://<IP_хоста>:8765/` (IP в консоли сервера)
- База и настройки (portable): подпапка `data/`

## Вариант 2: из исходников (разработка)

Требования: Python 3.11+, Node.js 18+ (для веб-клиента).

```bash
pip install -r client/requirements.txt
bash play.sh
```

В Windows **без Git Bash / WSL** (если `bash play.sh` пишет ошибку WSL):

```powershell
cd C:\path\to\farm-wars
.\play.bat
```

или:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\play.ps1
```

`bash play.sh` нужен только если установлен Git Bash или WSL с Linux.

Первый запуск соберёт `web/dist`, создаст `db/farm_wars.db`.

## Сборка релиза — что нужно

| Инструмент | Зачем |
|------------|--------|
| Python 3.11+ | сервер, PyInstaller |
| Node.js + npm | `web` → `dist` |
| Git Bash / WSL | скрипты `.sh` (на Windows) |

Опционально: MSVC или MinGW для C++ движка (`py tools/build_engine.py`). Без него работает **stub** — для игры достаточно.

## Переменные окружения

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `FARM_WARS_PORT` | `8765` | порт HTTP |
| `FARM_WARS_HOST` | `0.0.0.0` | интерфейс (LAN) |
| `FARM_WARS_OPEN_BROWSER` | `1` если есть UI | открыть браузер |
| `FARM_WARS_PORTABLE` | `1` в релизе | БД в `./data` |
| `FARM_WARS_DB_PATH` | — | свой путь к SQLite |

## Устранение проблем

- **Нет браузера** — откройте вручную `http://127.0.0.1:8765/`
- **Антивирус блокирует exe** — добавьте папку `FarmWars` в исключения или запускайте `bash play.sh` из исходников
- **Порт занят** — `set FARM_WARS_PORT=8770` перед запуском
