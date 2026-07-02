

from playwright.sync_api import Page
from .base import BaseChecker
import config

_FIREFOX_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) "
    "Gecko/20100101 Firefox/124.0"
)
_EXTRA_HEADERS = {
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Upgrade-Insecure-Requests": "1",
}


class FedresursChecker(BaseChecker):
    TITLE = "Сообщения о признаках банкротства (https://fedresurs.ru/)"
    URL_HOME = "https://fedresurs.ru/"

    def check(self, page: Page, inn: str) -> str:

        browser, fpage = self._new_secondary_browser(
            browser_type="firefox",
            user_agent=_FIREFOX_UA,
            extra_headers=_EXTRA_HEADERS,
        )
        try:
            self._goto(fpage, self.URL_HOME, wait_until="domcontentloaded")
            fpage.wait_for_timeout(6_000)
            self._close_modal_accept(fpage)


            body = self._safe_body(fpage).lower()
            if "404" in body or "not found" in body or "страница не найдена" in body:
                self._goto(fpage, self.URL_HOME, wait_until="domcontentloaded")
                fpage.wait_for_timeout(5_000)

            field = self._find_search_field(fpage)
            if field is None:
                print("  ⚠️  fedresurs.ru: поле поиска не найдено — сохраняем текущую страницу")
                return self._screenshot(fpage, "08_fedresurs_no_field.png")

            field.click()
            try:
                field.press("Control+A")
            except Exception:
                pass
            field.fill(inn)
            fpage.wait_for_timeout(800)
            self._submit_search(fpage, field, [
                "button:has-text('Найти')",
                "button:has-text('Поиск')",
                "button[type='submit']",
                "input[type='submit']",
                "[class*='search'] button",
                "button[class*='search']",
            ], wait_ms=config.TIMEOUT_LONG)

            self._wait_for_manual_captcha(fpage)
            fpage.wait_for_timeout(3_000)
            return self._screenshot(fpage, "08_fedresurs.png")
        finally:
            browser.close()

    def _safe_body(self, page: Page) -> str:
        try:
            return page.locator("body").inner_text(timeout=3_000)
        except Exception:
            return ""

    def _find_search_field(self, page: Page):
        selectors = [
            "input[placeholder*='Поиск']",
            "input[placeholder*='поиск']",
            "input[placeholder*='ИНН']",
            "input[placeholder*='ОГРН']",
            "input[name*='search']",
            "input[name*='query']",
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
