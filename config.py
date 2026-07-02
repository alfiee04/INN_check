

from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_CONFIG_PATH = os.environ.get("FILES_CHECK_CONFIG", "config.json")

VIEWPORT: dict = {"width": 1920, "height": 1080}
USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
HEADLESS: bool = False

TIMEOUT_NAV: int = 60_000
TIMEOUT_WAIT: int = 5_000
TIMEOUT_LONG: int = 10_000

SCREENSHOTS_DIR: str = "screenshots"
MANUAL_CAPTCHA_TIMEOUT_SEC: int = 180

COMPANIES: list[dict] = []




INN = ""
COMPANY_NAME = ""
EXECUTOR_NAME = ""
ADDRESS = ""
DIRECTOR_FIO = ""
PERSON_FIO = ""
PERSON_INN = ""
PASSPORT_SERIES = "4509"
PASSPORT_NUMBER = "123456"

PLAYWRIGHT = None

_config_path: str = DEFAULT_CONFIG_PATH
_raw: dict = {}


def load(path: str | None = None) -> None:
    global _config_path, _raw
    global VIEWPORT, USER_AGENT, HEADLESS
    global TIMEOUT_NAV, TIMEOUT_WAIT, TIMEOUT_LONG
    global SCREENSHOTS_DIR, MANUAL_CAPTCHA_TIMEOUT_SEC, COMPANIES

    _config_path = path or _config_path

    config_file = Path(_config_path)
    if not config_file.exists():
        raise FileNotFoundError(
            f"Не найден файл конфигурации: {config_file.resolve()}\n"
            f"Скопируйте config.example.json в config.json и заполните его "
            f"(вручную или через config_builder.html), затем запустите скрипт снова."
        )

    with config_file.open(encoding="utf-8") as f:
        _raw = json.load(f)

    browser = _raw.get("browser", {})
    VIEWPORT = browser.get("viewport", {"width": 1920, "height": 1080})
    USER_AGENT = browser.get("user_agent", USER_AGENT)
    HEADLESS = bool(browser.get("headless", False))

    timeouts = _raw.get("timeouts", {})
    TIMEOUT_NAV = int(timeouts.get("nav_ms", 60_000))
    TIMEOUT_WAIT = int(timeouts.get("wait_ms", 5_000))
    TIMEOUT_LONG = int(timeouts.get("long_ms", 10_000))

    SCREENSHOTS_DIR = _raw.get("screenshots_dir", "screenshots")
    MANUAL_CAPTCHA_TIMEOUT_SEC = int(_raw.get("manual_captcha_timeout_sec", 180))

    COMPANIES = _raw.get("companies", [])
    if not COMPANIES:
        raise ValueError(
            f"В файле {config_file} нет ни одной компании (ключ \"companies\" "
            f"пуст или отсутствует). Добавьте хотя бы одну запись — вручную "
            f"или через config_builder.html."
        )
    set_active_company(COMPANIES[0])


def set_active_company(company: dict) -> None:
    global INN, COMPANY_NAME, EXECUTOR_NAME, ADDRESS
    global DIRECTOR_FIO, PERSON_FIO, PERSON_INN, PASSPORT_SERIES, PASSPORT_NUMBER

    INN = str(company.get("inn", "")).strip()
    COMPANY_NAME = company.get("company_name", "")
    EXECUTOR_NAME = company.get("executor_name", "")
    ADDRESS = company.get("address", "")
    DIRECTOR_FIO = company.get("director_fio", "")
    PERSON_FIO = company.get("person_fio", "")
    PERSON_INN = company.get("person_inn", "")
    PASSPORT_SERIES = company.get("passport_series", "4509")
    PASSPORT_NUMBER = company.get("passport_number", "123456")


def find_company(inn: str) -> dict | None:
    inn = str(inn).strip()
    for c in COMPANIES:
        if str(c.get("inn", "")).strip() == inn:
            return c
    return None
def config_path() -> str:
    return _config_path

try:
    load()
except FileNotFoundError:
    pass
