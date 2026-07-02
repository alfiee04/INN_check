

from playwright.sync_api import Page
from .base import BaseChecker
import config


class BoNalogChecker(BaseChecker):
    TITLE = "Сдача бухгалтерской отчётности (https://bo.nalog.ru/)"
    URL   = "https://bo.nalog.ru/"

    def check(self, page: Page, inn: str) -> str:
        self._goto(page, self.URL, wait_until="domcontentloaded")
        page.wait_for_timeout(5_000)



        try:
            page.mouse.click(10, 10)
            page.wait_for_timeout(800)
        except Exception:
            pass


        self._close_bo_modal(page)


        inn_field = None
        for sel in [
            "input[name='query']",
            "input[id='query']",
            "input[placeholder*='ИНН']",
            "input[placeholder*='инн']",
            "input[placeholder*='ОГРН']",
            "input[type='search']",
            "input[type='text']",
        ]:
            try:
                loc = page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible(timeout=2_000):
                    inn_field = loc.first
                    break
            except Exception:
                pass

        if inn_field is None:
            raise RuntimeError("Поле поиска на bo.nalog.ru не найдено")

        inn_field.click()
        inn_field.fill(inn)
        page.wait_for_timeout(500)
        inn_field.press("Enter")
        page.wait_for_timeout(8_000)





        clicked = False
        try:

            inn_link = page.locator(f"a:has-text('{inn}')")
            if inn_link.count() > 0 and inn_link.first.is_visible(timeout=3_000):
                inn_link.first.click()
                clicked = True
        except Exception:
            pass

        if not clicked:

            for sel in [
                "table tbody tr:first-child td:first-child a",
                "a[href*='/organizations/']",
                "a[href*='organization']",
                ".organization-name a",
                ".company-name a",
                ".search-result a",
                "td:first-child a",
            ]:
                try:
                    lnk = page.locator(sel)
                    if lnk.count() > 0 and lnk.first.is_visible(timeout=2_000):
                        lnk.first.click()
                        clicked = True
                        break
                except Exception:
                    pass

        if clicked:
            page.wait_for_timeout(6_000)

        return self._screenshot(page, "03_bo_nalog.png")


    def _close_bo_modal(self, page: Page) -> None:
        for sel in [
            "button[aria-label='Закрыть']",
            ".close",
            ".notification-close",
            ".modal-close",
            "button:has-text('Продолжить')",
            "button:has-text('Принять')",
            "button:has-text('Согласен')",
            "button:has-text('OK')",
            "button:has-text('Ок')",
            ".notification__close",
            ".notification-popup .close",
            ".notification-popup button",
            ".modal__close",
            "[data-dismiss='modal']",
        ]:
            try:
                btn = page.locator(sel)
                if btn.count() > 0 and btn.first.is_visible(timeout=1_000):
                    btn.first.click()
                    page.wait_for_timeout(800)
            except Exception:
                pass


        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        except Exception:
            pass
