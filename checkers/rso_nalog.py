from playwright.sync_api import Page
from .base import BaseChecker
import config


class RsoNalogChecker(BaseChecker):
    TITLE = "Реестр субсидиарных ответчиков (https://www.nalog.gov.ru/rn77/rso/)"
    URL = "https://www.nalog.gov.ru/rn77/rso/"
    SEARCH_URL = "https://www.nalog.gov.ru/rn77/rso/search_o/"

    def check(self, page: Page, inn: str) -> str:
        target_inn = (getattr(config, "PERSON_INN", "").strip() or inn or "").strip()
        self._goto(page, self.URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2_000)
        self._close_modal_accept(page)
        self._open_search(page)

        field = self._fill_rso_inn(page, target_inn)
        old_url = page.url
        clicked = self._submit_search(page, field, [
            "a:has-text('Найти')",
            "button:has-text('Найти')",
            "input[type='submit'][value*='Найти']",
            "button[type='submit']",
            "input[type='submit']",
            "[role='button']:has-text('Найти')",
        ], wait_ms=2_000)
        self._wait_after_rso_submit(page, old_url, target_inn, clicked, field)
        return self._screenshot(page, "19_rso_nalog.png")

    def _open_search(self, page: Page) -> None:
        self._goto(page, self.SEARCH_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2_000)
        self._close_modal_accept(page)

    def _fill_rso_inn(self, page: Page, inn: str):
        selectors = [
            "input[aria-label*='ИНН']",
            "input[placeholder*='ИНН']",
            "input[name*='inn' i]",
            "input[id*='inn' i]",
            "input[type='search']",
            "input[type='text']",
            "input:not([type])",
        ]
        for sel in selectors:
            try:
                loc = page.locator(sel)
                for i in range(loc.count()):
                    item = loc.nth(i)
                    if item.is_visible(timeout=1_500) and item.is_enabled(timeout=1_500):
                        item.scroll_into_view_if_needed(timeout=1_500)
                        item.click()
                        item.fill(inn)
                        if inn in item.input_value(timeout=1_500):
                            return item
            except Exception:
                pass

        try:
            handle = page.evaluate_handle("""
                () => {
                    const labels = Array.from(document.querySelectorAll('label, div, span, p, td, th'));
                    const re = new RegExp('ИНН\\s*ФЛ/ЮЛ\\s*ответчика|ИНН', 'i');
                    const label = labels.find(el => re.test(el.textContent || ''));
                    if (!label) return null;
                    if (label.htmlFor) return document.getElementById(label.htmlFor);
                    const roots = [label.parentElement, label.closest('form'), document].filter(Boolean);
                    for (const root of roots) {
                        const field = root.querySelector('input[type="search"], input[type="text"], input:not([type])');
                        if (field) return field;
                    }
                    return null;
                }
            """)
            element = handle.as_element()
            if element:
                page.evaluate("""
                    ({ el, value }) => {
                        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
                        setter.call(el, value);
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                        el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, key: '0' }));
                    }
                """, {"el": element, "value": inn})
                return element
        except Exception:
            pass

        raise RuntimeError("Поле ИНН на сайте РСО не найдено")

    def _wait_after_rso_submit(self, page: Page, old_url: str, inn: str, clicked: bool, field) -> None:
        try:
            page.wait_for_load_state("networkidle", timeout=config.TIMEOUT_NAV)
        except Exception:
            try:
                page.wait_for_load_state("domcontentloaded", timeout=config.TIMEOUT_NAV)
            except Exception:
                pass
        page.wait_for_timeout(config.TIMEOUT_LONG)
        if self._rso_search_done(page, old_url, inn):
            return
        try:
            field.press("Enter")
            page.wait_for_timeout(config.TIMEOUT_LONG)
        except Exception:
            pass
        if self._rso_search_done(page, old_url, inn):
            return
        try:
            page.evaluate("""
                () => {
                    const btn = Array.from(document.querySelectorAll('button, a, input[type="submit"], [role="button"]'))
                        .find(el => /Найти/i.test(el.textContent || el.value || el.getAttribute('aria-label') || ''));
                    if (btn) btn.click();
                }
            """)
            page.wait_for_timeout(config.TIMEOUT_LONG)
        except Exception:
            pass

    def _rso_search_done(self, page: Page, old_url: str, inn: str) -> bool:
        try:
            body = page.locator("body").inner_text(timeout=3_000)
        except Exception:
            body = ""
        markers = ["Результ", "Найден", "Не найден", "запис", inn]
        return page.url != old_url or any(marker in body for marker in markers)
