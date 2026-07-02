from playwright.sync_api import Page
from .base import BaseChecker
import config


class BankrotFedresursChecker(BaseChecker):
    TITLE = "Информация о банкротстве (https://bankrot.fedresurs.ru/bankrupts?searchString)"
    URL = "https://bankrot.fedresurs.ru/bankrupts"

    def check(self, page: Page, inn: str) -> str:

        self._goto(page, f"{self.URL}?searchString={inn}", wait_until="domcontentloaded")
        page.wait_for_timeout(7_000)
        self._close_modal_accept(page)

        field = self._find_field(page)
        if field is not None:
            field.click()
            try:
                field.press("Control+A")
            except Exception:
                pass
            field.fill(inn)
            page.wait_for_timeout(800)
            self._submit_search(page, field, [
                "button:has-text('Найти')",
                "button:has-text('Поиск')",
                "button[type='submit']",
                "input[type='submit']",
                "[class*='search'] button",
                "button[class*='search']",
            ], wait_ms=config.TIMEOUT_LONG)
        else:
            print("  ⚠️  bankrot.fedresurs.ru: поле поиска не найдено — скриншот текущей страницы")

        self._wait_for_manual_captcha(page)
        try:
            page.wait_for_selector("text=Найдено, text=Ничего не найдено, text=Нет результатов, .bankrupt, .card, table", timeout=10_000)
        except Exception:
            page.wait_for_timeout(4_000)
        return self._screenshot(page, "09_bankrot_fedresurs.png")

    def _find_field(self, page: Page):
        selectors = [
            "input[placeholder*='Поиск']",
            "input[placeholder*='поиск']",
            "input[placeholder*='ИНН']",
            "input[name='searchString']",
            "input[name*='search']",
            "input[type='search']",
            "input[type='text']",
            "textarea[placeholder*='Поиск']",
        ]
        for sel in selectors:
            try:
                loc = page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible(timeout=2_000):
                    return loc.first
            except Exception:
                pass
        return None
