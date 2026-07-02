

from playwright.sync_api import Page
from .base import BaseChecker
import config


class ZakupkiRnpChecker(BaseChecker):
    TITLE = (
        "Реестр недобросовестных поставщиков "
        "(https://zakupki.gov.ru/epz/dishonestsupplier/search/results.html)"
    )
    URL = "https://zakupki.gov.ru/epz/dishonestsupplier/search/results.html"

    def check(self, page: Page, inn: str) -> str:
        page.context.grant_permissions([])

        self._goto(page, self.URL)
        page.wait_for_timeout(8_000)

        self._close_modal_accept(page)
        self._close_cert_modal(page)

        inn_selectors = [
            "input#participantInn",
            "input[name='participantInn']",
            "input[name='inn']",
            "input[id='inn']",
            "input[placeholder*='ИНН']",
        ]
        self._fill_inn(page, inn, inn_selectors)

        inn_loc = page.locator(
            "input#participantInn, input[name='participantInn'], "
            "input[name='inn'], input[id='inn']"
        ).first
        self._submit(page, inn_loc, [
            "button.search__btn",
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Найти')",
        ])
        page.wait_for_timeout(config.TIMEOUT_LONG)

        return self._screenshot(page, "02_zakupki_rnp.png")
