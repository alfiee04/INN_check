

from playwright.sync_api import Page
from .base import BaseChecker
import config


class TransparentBizChecker(BaseChecker):
    TITLE = "Сервис «Прозрачный бизнес» ФНС (https://pb.nalog.ru/search.html)"
    URL   = "https://pb.nalog.ru/search.html"

    def check(self, page: Page, inn: str) -> str:
        self._goto(page, self.URL)
        page.wait_for_timeout(config.TIMEOUT_WAIT)

        self._close_modal(page)


        page.wait_for_selector(
            "input[name='queryAll'], input[placeholder*='ИНН'], input[placeholder*='инн']",
            timeout=15_000,
        )

        self._fill_inn(page, inn, [
            "input[name='queryAll']",
            "input[placeholder*='ИНН']",
            "input[placeholder*='инн']",
            "input[type='text']",
        ])

        inn_loc = page.locator("input[name='queryAll'], input[placeholder*='ИНН']").first
        self._submit(page, inn_loc, [
            "button[type='submit']",
            "button:has-text('Найти')",
            ".search-btn",
        ])


        page.wait_for_timeout(config.TIMEOUT_LONG)


        clicked = False


        try:
            lnk = page.locator(f"a:has-text('{inn}')")
            if lnk.count() > 0 and lnk.first.is_visible(timeout=3_000):
                lnk.first.click()
                clicked = True
        except Exception:
            pass

        if not clicked:

            for sel in [

                ".search-res-list .search-res-item:first-child",
                ".card-list .card-item:first-child",
                ".result-item:first-child",
                "a.company-link",
                "a[href*='/company/']",
                "a[href*='/organization/']",
                "a[href*='/person/']",

                ".search-results a:first-child",
                "ul.results li:first-child a",
                "table tbody tr:first-child a",
                ".result a",
            ]:
                try:
                    el = page.locator(sel)
                    if el.count() > 0 and el.first.is_visible(timeout=2_000):
                        el.first.click()
                        clicked = True
                        break
                except Exception:
                    pass

        if clicked:

            page.wait_for_timeout(6_000)

        return self._screenshot(page, "05_pb_nalog.png")
