

from playwright.sync_api import Page
from .base import BaseChecker
import config


class VestnikGosregChecker(BaseChecker):
    TITLE = "Информация о юридическом состоянии (https://www.vestnik-gosreg.ru/search/)"
    URL   = "https://www.vestnik-gosreg.ru/search/"

    def check(self, page: Page, inn: str) -> str:
        self._goto(page, self.URL)
        page.wait_for_timeout(config.TIMEOUT_WAIT)

        self._close_modal(page)

        self._fill_inn(page, inn, [
            "input[name='query']",
            "input[name='search']",
            "input[name='inn']",
            "input[placeholder*='ИНН']",
            "input[placeholder*='ОГРН']",
            "input[type='text']",
            "input[type='search']",
        ])

        inn_loc = page.locator(
            "input[name='query'], input[name='search'], input[name='inn'], input[type='text']"
        ).first
        self._submit(page, inn_loc, [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Найти')",
            "button:has-text('Поиск')",
        ])
        page.wait_for_timeout(config.TIMEOUT_LONG)

        return self._screenshot(page, "04_vestnik_gosreg.png")
