

from playwright.sync_api import Page
from .base import BaseChecker
import config

_FIREFOX_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) "
    "Gecko/20100101 Firefox/124.0"
)


class AddressSearchChecker(BaseChecker):
    TITLE = "Поиск адреса организации в Яндексе (отдельный браузер Firefox)"
    URL   = "https://yandex.ru"

    def check(self, page: Page, inn: str) -> str:


        address = config.ADDRESS

        browser, fpage = self._new_secondary_browser(
            browser_type="firefox", user_agent=_FIREFOX_UA
        )

        try:
            self._goto(fpage, self.URL, wait_until="domcontentloaded")
            fpage.wait_for_timeout(3_000)


            for sel in [
                "button:has-text('Принять')",
                "button:has-text('Хорошо')",
                "button:has-text('Понятно')",
                "button:has-text('Да')",
                ".gdpr-popup-v3__button",
                ".cookie-confirm__button",
                "[data-t='button:accept']",
            ]:
                try:
                    btn = fpage.locator(sel)
                    if btn.count() > 0 and btn.first.is_visible(timeout=2_000):
                        btn.first.click()
                        fpage.wait_for_timeout(800)
                        break
                except Exception:
                    pass






            search_selectors = [
                "input[name='text']",
                "input#text",
                "input.search3__input",
                "input[class*='search__input']",
                "input[class*='search3__input']",
                "input[class*='input__control']",
                "input[aria-label='Запрос']",
                "input[placeholder*='Найдётся всё']",
                "input[type='text']",
            ]
            combined_selector = ", ".join(search_selectors)

            search_field = None
            try:



                fpage.wait_for_selector(
                    combined_selector, state="visible", timeout=20_000
                )
            except Exception:
                pass

            for sel in search_selectors:
                try:
                    loc = fpage.locator(sel)
                    if loc.count() > 0 and loc.first.is_visible(timeout=1_500):
                        search_field = loc.first
                        break
                except Exception:
                    pass

            if search_field is None:



                print(
                    f"  ⚠️  {self.TITLE}: поле поиска не найдено — "
                    "сохраняем скриншот текущей страницы"
                )
                return self._screenshot(fpage, "11_address_search_yandex.png")

            search_field.click()
            search_field.fill(address)
            fpage.wait_for_timeout(600)
            search_field.press("Enter")


            try:
                fpage.wait_for_selector(
                    ".serp-list, .organic, li.serp-item, "
                    "[data-cid], .search-result__snippet",
                    timeout=15_000,
                )
            except Exception:
                pass

            fpage.wait_for_timeout(2_000)

            return self._screenshot(fpage, "11_address_search_yandex.png")
        finally:
            browser.close()
