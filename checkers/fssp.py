

from playwright.sync_api import Page
from .base import BaseChecker
import config

_CAPTCHA_SIGNS = [
    "iframe[src*='captcha']",
    "iframe[src*='recaptcha']",
    "iframe[src*='hcaptcha']",
    ".g-recaptcha",
    "#captcha",
    "input[name='captcha']",
    "img[src*='captcha']",
    "div.captcha",
    "div[class*='captcha']",
]




_INN_FIELD_SELECTORS = [
    ".e-input_inn input",
    "input[data-inputgroup='.e-input_inn']",
    "input[name='is[inn]']",
    "input[id='is-inn-input']",
    "input[placeholder*='ИНН']",
    "input[class*='inn']",
]


class FsspChecker(BaseChecker):
    TITLE = "Банк данных исполнительных производств (https://fssp.gov.ru/iss/ip)"
    URL = "https://fssp.gov.ru/iss/ip"

    def check(self, page: Page, inn: str) -> str:
        self._goto(page, self.URL, wait_until="domcontentloaded")
        page.wait_for_timeout(5_000)

        self._close_modal_accept(page)


        self._select_inn_search_mode(page)


        inn_field = self._wait_for_inn_field(page)
        if inn_field is None:


            print(
                f"  ⚠️  {self.TITLE}: поле ИНН не появилось после выбора "
                "режима поиска — сохраняем скриншот как есть"
            )
            return self._screenshot(page, "09_fssp.png")

        inn_field.click()
        inn_field.fill("")
        inn_field.fill(inn)
        page.wait_for_timeout(600)


        self._press_find(page, inn_field)


        captcha_found = False
        for sel in _CAPTCHA_SIGNS:
            try:
                el = page.locator(sel)
                if el.count() > 0 and el.first.is_visible(timeout=1_500):
                    captcha_found = True
                    break
            except Exception:
                pass

        if captcha_found:
            self._wait_for_manual_captcha(page)

            self._press_find(page, inn_field)

        return self._screenshot(page, "11_fssp.png")


    def _press_find(self, page: Page, inn_field) -> None:
        self._submit_search(page, inn_field, [
            "input#btn-sbm",
            "input[id='btn-sbm']",
            "input[value='Найти'].c-btn--gold",
            "input[type='submit'][value='Найти']",
            "button:has-text('Найти')",
            ".c-btn:has-text('Найти')",
        ], wait_ms=config.TIMEOUT_LONG)


    def _select_inn_search_mode(self, page: Page) -> None:
        label = page.locator("label:has(input#r5)")
        radio = page.locator("input#r5, input[value='5'][name='is[variant]']")


        try:
            if label.count() > 0:
                label.first.scroll_into_view_if_needed()
                label.first.click(timeout=3_000)
                page.wait_for_timeout(1_000)
                if self._inn_field_present(page):
                    return
        except Exception:
            pass


        try:
            if radio.count() > 0:
                radio.first.scroll_into_view_if_needed()
                radio.first.click(timeout=3_000)
                page.wait_for_timeout(1_000)
                if self._inn_field_present(page):
                    return
        except Exception:
            pass



        try:
            if radio.count() > 0:
                radio.first.click(force=True, timeout=3_000)
                page.wait_for_timeout(1_000)
                if self._inn_field_present(page):
                    return
        except Exception:
            pass


        try:
            if radio.count() > 0:
                radio.first.check(force=True, timeout=3_000)
                page.wait_for_timeout(1_000)
                if self._inn_field_present(page):
                    return
        except Exception:
            pass


        try:
            text_label = page.locator(
                "label:has-text('Поиск по ИНН юридического лица')"
            )
            if text_label.count() > 0:
                text_label.first.click(timeout=3_000)
                page.wait_for_timeout(1_000)
        except Exception:
            pass

    def _inn_field_present(self, page: Page) -> bool:
        for sel in _INN_FIELD_SELECTORS:
            try:
                loc = page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible(timeout=800):
                    return True
            except Exception:
                pass
        return False

    def _wait_for_inn_field(self, page: Page):
        combined = ", ".join(_INN_FIELD_SELECTORS)
        try:
            page.wait_for_selector(combined, state="visible", timeout=8_000)
        except Exception:
            pass

        for sel in _INN_FIELD_SELECTORS:
            try:
                loc = page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible(timeout=1_000):
                    return loc.first
            except Exception:
                pass
        return None
