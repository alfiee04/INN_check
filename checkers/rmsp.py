

from playwright.sync_api import Page
from .base import BaseChecker
import config


class RmspChecker(BaseChecker):
    TITLE = "Нахождение в реестре субъектов МСП (https://rmsp.nalog.ru/)"
    URL   = "https://rmsp.nalog.ru/"

    def check(self, page: Page, inn: str) -> str:
        self._goto(page, self.URL)
        page.wait_for_timeout(config.TIMEOUT_WAIT)

        self._fill_inn(page, inn, [
            "input[name='query']",
            "input[id='query']",
            "input[placeholder*='ИНН']",
            "input[placeholder*='инн']",
        ])

        self._submit(page, page.locator("input[name='query']").first, [
            "button[type='submit']",
            "input[type='submit']",
        ])
        page.wait_for_timeout(config.TIMEOUT_LONG)

        return self._screenshot(page, "01_rmsp.png")
