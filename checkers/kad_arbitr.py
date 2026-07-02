

from playwright.sync_api import Page
from .base import BaseChecker
import config


class KadArbitrChecker(BaseChecker):
    TITLE = "Информация о банкротстве — Картотека арбитражных дел (https://kad.arbitr.ru/)"
    URL = "https://kad.arbitr.ru/"

    def check(self, page: Page, inn: str) -> str:
        self._goto(page, self.URL, wait_until="domcontentloaded")
        page.wait_for_timeout(8_000)
        self._close_modal_accept(page)

        field = self._find_participant_field(page)
        if field is None:
            print("  ⚠️  kad.arbitr.ru: поле участника не найдено — сохраняем страницу")
            return self._screenshot(page, "10_kad_arbitr_no_field.png")

        field.click()
        try:
            field.press("Control+A")
        except Exception:
            pass
        field.fill(inn)
        page.wait_for_timeout(800)
        try:
            field.press("Tab")
        except Exception:
            pass
        page.wait_for_timeout(500)

        clicked = self._submit_search(page, field, [
            "button#b-form-submit",
            "#b-form-submit",
            "button[id='b-form-submit']",
            "button[type='submit']",
            "button:has-text('Найти')",
            ".b-form-submit",
            ".b-button:has-text('Найти')",
        ], wait_ms=3_000)

        if not clicked:
            try:
                page.evaluate("""
                    () => {
                        const btn = document.querySelector('#b-form-submit') ||
                                    [...document.querySelectorAll('button,input[type=submit]')]
                                    .find(x => /найти|поиск/i.test(x.innerText || x.value || ''));
                        if (btn) btn.click();
                    }
                """)
                page.wait_for_timeout(3_000)
            except Exception:
                pass


        try:
            if page.locator("#b-form-submit").count() > 0:
                field.focus()
                field.press("Enter")
                page.wait_for_timeout(3_000)
        except Exception:
            pass


        try:
            page.wait_for_selector(".b-cases, .b-results, table, text=Найдено, text=Нет результатов", timeout=15_000)
        except Exception:
            page.wait_for_timeout(config.TIMEOUT_LONG)

        return self._screenshot(page, "10_kad_arbitr.png")

    def _find_participant_field(self, page: Page):
        selectors = [
            "textarea[placeholder*='название']",
            "textarea[placeholder*='ИНН']",
            "textarea[placeholder*='ОГРН']",
            "textarea.g-ph",
            "textarea",
            "input[placeholder*='название']",
            "input[placeholder*='ИНН']",
        ]
        for sel in selectors:
            try:
                loc = page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible(timeout=3_000):
                    return loc.first
            except Exception:
                pass
        return None
