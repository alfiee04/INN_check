
from playwright.sync_api import Page, TimeoutError as PWTimeout
from .base import BaseChecker
import config


class MinjustChecker(BaseChecker):
    TITLE = "Реестр иностранных агентов Минюст (https://minjust.gov.ru/ru/pages/reestr-inostryannykh-agentov/)"
    URL   = "https://minjust.gov.ru/ru/pages/reestr-inostryannykh-agentov/"

    def check(self, page: Page, inn: str) -> str:

        self._goto(page, self.URL, wait_until="domcontentloaded")
        page.wait_for_timeout(5_000)

        self._close_modal_accept(page)


        search_field = None
        for sel in [
            "input#registry_search",
            "input[id='registry_search']",
            ".regisrty_search-container input[type='search']",
            "input[placeholder='Поиск']",
        ]:
            try:
                loc = page.locator(sel)
                loc.first.wait_for(state="visible", timeout=10_000)
                search_field = loc.first
                break
            except Exception:
                pass

        if search_field is None:

            print(f"  ⚠️  {self.TITLE}: поле поиска не найдено — сохраняем скриншот")
            return self._screenshot(page, "10_minjust.png")


        search_field.click()
        search_field.fill("")
        search_field.type(inn, delay=80)



        try:
            page.wait_for_function(
                """(query) => {
                    // Ищем любой контейнер с результатами или «ничего не найдено»
                    const items = document.querySelectorAll(
                        '.registry-item, .registry_item, .registry-list__item, '
                        + 'tr.registry-row, .b-registry__item, '
                        + '[class*="registry"][class*="item"], '
                        + '[class*="registry"][class*="row"]'
                    );
                    const noResult = document.querySelector(
                        '.no-result, .noresult, [class*="no-result"], [class*="empty"]'
                    );
                    return items.length > 0 || noResult !== null;
                }""",
                arg=inn,
                timeout=8_000,
            )
        except PWTimeout:

            page.wait_for_timeout(3_000)


        return self._screenshot(page, "10_minjust.png")
