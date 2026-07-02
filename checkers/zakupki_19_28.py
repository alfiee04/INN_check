

from playwright.sync_api import Page
from .base import BaseChecker
import config

_URL = (
    "https://zakupki.gov.ru/epz/main/public/document/view.html"
    "?searchString=&sectionId=2369&strictEqual=false"
)


class Zakupki1928Checker(BaseChecker):
    TITLE = (
        "Привлечение к административной ответственности по ст. 19.28 КоАП РФ "
        "(https://zakupki.gov.ru — sectionId=2369)"
    )
    URL = _URL

    def check(self, page: Page, inn: str) -> str:

        page.context.grant_permissions([])

        self._goto(page, self.URL)
        page.wait_for_timeout(8_000)

        self._close_modal_accept(page)
        self._close_cert_modal(page)

        self._fill_inn(page, inn, [
            "input[name='searchString']",
            "input[id='searchString']",
            "input.search-input",
            "input[placeholder*='Поиск']",
            "input[placeholder*='ИНН']",
            "input[type='search']",
        ])

        inn_loc = page.locator(
            "input[name='searchString'], input[id='searchString'], input.search-input"
        ).first
        self._submit(page, inn_loc, [
            "button[type='submit']",
            "button.search__btn",
            "input[type='submit']",
            "button:has-text('Найти')",
        ])
        page.wait_for_timeout(config.TIMEOUT_LONG)

        return self._screenshot(page, "07_zakupki_19_28.png")
