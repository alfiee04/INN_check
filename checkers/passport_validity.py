from playwright.sync_api import Page
from .base import BaseChecker
import config
import time


class PassportValidityChecker(BaseChecker):
    TITLE = "Проверка действительности паспорта (https://xn----7sbbags9a3agcgbedhnu.xn--p1ai/)"
    URL = "https://xn----7sbbags9a3agcgbedhnu.xn--p1ai/"

    def check(self, page: Page, inn: str) -> str:
        self._goto(page, self.URL, wait_until="domcontentloaded")
        page.wait_for_timeout(5_000)
        self._close_modal_accept(page)


        series = (getattr(config, "PASSPORT_SERIES", "") or "4509").strip()
        number = (getattr(config, "PASSPORT_NUMBER", "") or "123456").strip()

        text_fields = self._visible_text_fields(page)
        if len(text_fields) >= 2:
            text_fields[0].click()
            text_fields[0].fill(series)
            page.wait_for_timeout(300)
            text_fields[1].click()
            text_fields[1].fill(number)
        else:
            self._fill_by_selectors(page, series, [
                "input[name*='series' i]", "input[name*='seria' i]",
                "input[placeholder*='сер' i]", "input[id*='series' i]",
            ])
            self._fill_by_selectors(page, number, [
                "input[name*='number' i]", "input[name*='nomer' i]",
                "input[placeholder*='номер' i]", "input[id*='number' i]",
            ])

        page.wait_for_timeout(800)
        self._wait_for_manual_captcha(page)
        self._submit_search(page, text_fields[0] if text_fields else None, [
            "button:has-text('Проверить')",
            "button:has-text('Найти')",
            "input[value*='Проверить']",
            "input[value*='Найти']",
            "button[type='submit']",
            "input[type='submit']",
        ], wait_ms=config.TIMEOUT_LONG)




        self._wait_for_results(page)
        page.wait_for_timeout(10_000)

        return self._screenshot(page, "16_passport_validity.png")

    def _wait_for_results(self, page: Page, timeout: int = 60_000):


        self._wait_for_loading_to_disappear(page)


        start_time = time.time()
        while time.time() - start_time < timeout / 1000:

            if self._is_loading_present(page):
                self._wait_for_loading_to_disappear(page)
                continue


            result_selectors = [
                "div:has-text('действителен')",
                "div:has-text('недействителен')",
                "div:has-text('действительный')",
                "div:has-text('недействительный')",
                "div:has-text('валидный')",
                "div:has-text('не валидный')",
                "div:has-text('действительности')",
                "div:has-text('подлинность')",
                "div:has-text('статус')",
                ".result",
                ".status",
                "[class*='result']",
                "[class*='status']",
                "div:has-text('Проверка завершена')",
                "div:has-text('Результат проверки')",
            ]

            for selector in result_selectors:
                try:
                    loc = page.locator(selector)
                    if loc.count() > 0 and loc.first.is_visible(timeout=100):

                        page.wait_for_timeout(2_000)
                        return
                except Exception:
                    pass


            error_selectors = [
                "div:has-text('ошибка')",
                "div:has-text('Error')",
                "div:has-text('не найдено')",
                "div:has-text('не найден')",
                "div:has-text('не действителен')",
            ]

            for selector in error_selectors:
                try:
                    loc = page.locator(selector)
                    if loc.count() > 0 and loc.first.is_visible(timeout=100):
                        page.wait_for_timeout(2_000)
                        return
                except Exception:
                    pass


            timer_selectors = [
                "div:has-text('секунд')",
                "div:has-text('сек')",
                "div:has-text('Осталось')",
                "div:has-text('wait')",
            ]

            timer_found = False
            for selector in timer_selectors:
                try:
                    loc = page.locator(selector)
                    if loc.count() > 0 and loc.first.is_visible(timeout=100):
                        timer_found = True
                        text = loc.first.text_content() or ""

                        page.wait_for_timeout(8_000)
                        break
                except Exception:
                    pass

            if timer_found:
                continue


            current_url = page.url
            if "result" in current_url or "status" in current_url or "check" in current_url:
                page.wait_for_timeout(3_000)
                return


            page.wait_for_timeout(500)


        page.wait_for_timeout(5_000)

    def _is_loading_present(self, page: Page) -> bool:
        loading_selectors = [
            ".loader",
            ".spinner",
            ".loading",
            "[class*='load']",
            "[class*='spin']",
            "div:has-text('Загрузка')",
            "div:has-text('Loading')",
            "div:has-text('Пожалуйста, подождите')",
            "div[role='progressbar']",
            "svg[class*='spinner']",
        ]

        for selector in loading_selectors:
            try:
                loc = page.locator(selector)
                if loc.count() > 0 and loc.first.is_visible(timeout=200):
                    return True
            except Exception:
                pass
        return False

    def _wait_for_loading_to_disappear(self, page: Page, timeout: int = 30_000):
        loading_selectors = [
            ".loader",
            ".spinner",
            ".loading",
            "[class*='load']",
            "[class*='spin']",
            "div:has-text('Загрузка')",
            "div:has-text('Loading')",
            "div:has-text('Пожалуйста, подождите')",
            "div[role='progressbar']",
            "svg[class*='spinner']",
        ]

        start_time = time.time()
        while time.time() - start_time < timeout / 1000:
            loading_found = False
            for selector in loading_selectors:
                try:
                    loc = page.locator(selector)
                    if loc.count() > 0 and loc.first.is_visible(timeout=100):
                        loading_found = True
                        break
                except Exception:
                    pass

            if not loading_found:
                return

            page.wait_for_timeout(500)


        page.wait_for_timeout(3_000)

    def _visible_text_fields(self, page: Page):
        result = []
        try:
            fields = page.locator("input[type='text'], input[type='tel'], input:not([type])")
            for i in range(fields.count()):
                item = fields.nth(i)
                try:
                    if item.is_visible(timeout=500) and item.is_enabled(timeout=500):
                        result.append(item)
                except Exception:
                    pass
        except Exception:
            pass
        return result

    def _fill_by_selectors(self, page: Page, value: str, selectors: list[str]) -> bool:
        for sel in selectors:
            try:
                loc = page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible(timeout=1_000):
                    loc.first.click()
                    loc.first.fill(value)
                    return True
            except Exception:
                pass
        return False

    def _close_modal_accept(self, page: Page):
        try:

            accept_selectors = [
                "button:has-text('Принять')",
                "button:has-text('OK')",
                "button:has-text('Accept')",
                "button:has-text('Закрыть')",
                "button:has-text('Close')",
                ".modal button",
                ".popup button",
                "[class*='close']",
            ]

            for selector in accept_selectors:
                try:
                    loc = page.locator(selector)
                    if loc.count() > 0 and loc.first.is_visible(timeout=500):
                        loc.first.click()
                        page.wait_for_timeout(500)
                        break
                except Exception:
                    pass
        except Exception:
            pass

    def _wait_for_manual_captcha(self, page: Page):

        captcha_selectors = [
            "iframe[src*='captcha']",
            "div[id*='captcha']",
            "img[alt*='captcha']",
            "div:has-text('капча')",
            "div:has-text('captcha')",
        ]

        for selector in captcha_selectors:
            try:
                loc = page.locator(selector)
                if loc.count() > 0 and loc.first.is_visible(timeout=2_000):

                    print("Обнаружена капча. Ожидаем ручного ввода...")
                    page.wait_for_timeout(60_000)
                    break
            except Exception:
                pass
