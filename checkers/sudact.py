from playwright.sync_api import Page
from .base import BaseChecker
import config


class SudactChecker(BaseChecker):
    TITLE = "Проверка на судимость через открытые источники (https://sudact.ru/regular/)"
    URL = "https://sudact.ru/regular/"

    def check(self, page: Page, inn: str) -> str:
        query = getattr(config, "DIRECTOR_FIO", "").strip() or getattr(config, "PERSON_FIO", "").strip()

        self._goto(page, self.URL, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        self._close_modal_accept(page)

        if not query:
            print("  ⚠️  DIRECTOR_FIO/PERSON_FIO не задан — сохраняем страницу для ручного ввода")
            return self._screenshot(page, "18_sudact_manual.png")

        field = self._fill_text_document(page, query)
        self._submit_search(page, field)

        return self._screenshot(page, "18_sudact.png")

    def _fill_text_document(self, page: Page, query: str):
        field = page.locator("#id_regular-txt")

        field.wait_for(state="visible", timeout=15000)
        field.scroll_into_view_if_needed()
        field.click()
        field.fill("")
        field.fill(query)

        page.wait_for_timeout(500)

        value = field.input_value()

        if value.strip() != query:
            raise RuntimeError("Не удалось заполнить поле 'Текст документа' на Sudact")

        return field

    def _submit_search(self, page: Page, field) -> None:
        old_url = page.url

        search_btn = page.locator("input.f-submit[value='Найти']")
        search_btn.wait_for(state="visible", timeout=10000)
        search_btn.scroll_into_view_if_needed()
        search_btn.click()

        self._wait_after_submit(page, old_url)

        if page.url == old_url:
            field.press("Enter")
            self._wait_after_submit(page, old_url)

        if page.url == old_url:
            page.evaluate("""
                () => {
                    const form = document.querySelector('#id_regular-txt')?.closest('form');
                    if (form) form.submit();
                }
            """)
            self._wait_after_submit(page, old_url)

    def _wait_after_submit(self, page: Page, old_url: str) -> None:
        try:
            page.wait_for_load_state("domcontentloaded", timeout=config.TIMEOUT_NAV)
        except Exception:
            pass

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        page.wait_for_timeout(5000)