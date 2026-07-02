

import os
import time
import traceback
import threading
import sys
from abc import ABC, abstractmethod
from playwright.sync_api import Page

import config


class SkipSite(Exception):
    pass


class _SlowLoadDialog:
    def __init__(self, title: str, threshold_sec: int = 25, ask_timeout: int = 30):
        self.title        = title
        self.threshold    = threshold_sec
        self.ask_timeout  = ask_timeout
        self.should_skip  = False
        self._nav_done    = threading.Event()
        self._thread      = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def nav_finished(self):
        self._nav_done.set()

    def _run(self):

        finished = self._nav_done.wait(timeout=self.threshold)
        if finished:
            return


        prompt = (
            f"\n{'='*60}\n"
            f"⏳  Сайт долго загружается:\n"
            f"    {self.title[:68]}\n"
            f"{'='*60}\n"
            f"  [д / y / да]  — продолжать ждать\n"
            f"  [Enter / н]   — пропустить и перейти дальше\n"
            f"  Авто-пропуск через {self.ask_timeout} сек...\n"
            f"  Ваш выбор: "
        )
        answer = [None]

        def _read():
            try:
                answer[0] = input(prompt).strip().lower()
            except Exception:
                answer[0] = ""

        t = threading.Thread(target=_read, daemon=True)
        t.start()
        t.join(timeout=self.ask_timeout)

        if t.is_alive():

            sys.stdout.write("\n  ⏭️  Время вышло, переходим дальше…\n")
            sys.stdout.flush()
            self.should_skip = True
        else:
            raw = answer[0] or ""
            if raw in ("д", "y", "да", "yes"):
                self.should_skip = False
                sys.stdout.write("  ⏳  Продолжаем ждать…\n")
                sys.stdout.flush()

                self._nav_done.wait(timeout=self.ask_timeout)
            else:
                self.should_skip = True
                sys.stdout.write("  ⏭️  Пропускаем сайт…\n")
                sys.stdout.flush()

    def join(self):
        self._thread.join(timeout=1)


class BaseChecker(ABC):
    TITLE: str = "Без названия"
    URL:   str = ""

    SLOW_THRESHOLD_SEC: int = 25
    ASK_TIMEOUT_SEC:    int = 30


    def run(self, page: Page, inn: str) -> tuple:
        try:
            path = self.check(page, inn)
            if path is None:
                print(f"  ⚠️  {self.TITLE}: раздел без автоматического скриншота")
                return self.TITLE, None, "MANUAL: раздел предусмотрен ТЗ, заполняется вручную"
            print(f"  ✅  {self.TITLE}")
            return self.TITLE, path, None
        except SkipSite as s:
            msg = f"Пропущено: {s}"
            print(f"  ⏭️  {self.TITLE}: {msg}")
            return self.TITLE, None, msg
        except Exception as exc:
            short = str(exc)[:200]
            print(f"  ❌  {self.TITLE}: {short}")
            traceback.print_exc()
            return self.TITLE, None, short


    @abstractmethod
    def check(self, page: Page, inn: str) -> str:
        pass


    def _goto(self, page: Page, url: str,
              wait_until: str = "domcontentloaded") -> None:
        dialog = _SlowLoadDialog(
            title         = self.TITLE,
            threshold_sec = self.SLOW_THRESHOLD_SEC,
            ask_timeout   = self.ASK_TIMEOUT_SEC,
        )
        dialog.start()

        nav_exc = None
        try:
            page.goto(url, timeout=config.TIMEOUT_NAV, wait_until=wait_until)
        except Exception as e:
            nav_exc = e
        finally:
            dialog.nav_finished()
            dialog.join()

        if dialog.should_skip:

            try:
                page.evaluate("window.stop()")
            except Exception:
                pass
            raise SkipSite(f"пользователь пропустил {url}")

        if nav_exc is not None:
            raise nav_exc


    def _screenshot(self, page: Page, filename: str) -> str:
        os.makedirs(config.SCREENSHOTS_DIR, exist_ok=True)
        path = os.path.join(config.SCREENSHOTS_DIR, filename)
        page.screenshot(path=path, full_page=True)
        return path

    def _close_modal(self, page: Page) -> None:
        for sel in [
            "button[aria-label='Закрыть']",
            "button[aria-label='Close']",
            ".modal-close",
            ".close",
            ".cookie-close",
            "button:has-text('Закрыть')",
            "button:has-text('×')",
            "[data-dismiss='modal']",
        ]:
            try:
                btn = page.locator(sel)
                if btn.count() > 0 and btn.first.is_visible(timeout=1_000):
                    btn.first.click()
                    page.wait_for_timeout(800)
                    break
            except Exception:
                pass

    def _close_modal_accept(self, page: Page) -> None:
        self._close_modal(page)
        for sel in [
            "button:has-text('Принять')",
            "button:has-text('Принять все')",
            "button:has-text('Согласен')",
            "button:has-text('Agree')",
            "button:has-text('Понятно')",
            "button:has-text('OK')",
            "button:has-text('Продолжить')",
            ".cookie-banner__accept",
            ".cookie__accept",
            ".b-modal__close",
            ".modal .close",
            "button[aria-label='Закрыть']",
            "[data-dismiss='modal']",
            ".modal-backdrop",
        ]:
            try:
                btn = page.locator(sel)
                if btn.count() > 0 and btn.first.is_visible(timeout=1_500):
                    btn.first.click()
                    page.wait_for_timeout(800)
            except Exception:
                pass

    def _close_cert_modal(self, page: Page) -> None:


        try:
            heading = page.get_by_text("Установите сертификаты Минцифры РФ", exact=False)
            if heading.count() == 0 or not heading.first.is_visible(timeout=1_500):
                return
        except Exception:
            return


        for sel in [
            "text=×",
            "[class*='close']",
            "[class*='Close']",
            "svg[class*='close']",
            "button[aria-label='Закрыть']",
            "button[aria-label='Close']",
            "[aria-label='Закрыть']",
            "[aria-label='Close']",
            ".modal-close",
            ".close",
        ]:
            try:
                btn = page.locator(sel)
                if btn.count() > 0 and btn.first.is_visible(timeout=1_500):
                    btn.first.click()
                    page.wait_for_timeout(800)

                    still_open = page.get_by_text(
                        "Установите сертификаты Минцифры РФ", exact=False
                    )
                    if still_open.count() == 0 or not still_open.first.is_visible(timeout=1_000):
                        return
            except Exception:
                pass




        try:
            box = heading.first.bounding_box()
            modal_box = page.locator(
                "div:has-text('Установите сертификаты Минцифры РФ')"
            ).first.bounding_box()
            if box and modal_box:
                x = modal_box["x"] + modal_box["width"] - 24
                y = box["y"] + box["height"] / 2
                page.mouse.click(x, y)
                page.wait_for_timeout(800)
                still_open = page.get_by_text(
                    "Установите сертификаты Минцифры РФ", exact=False
                )
                if still_open.count() == 0 or not still_open.first.is_visible(timeout=1_000):
                    return
        except Exception:
            pass


        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        except Exception:
            pass


    def _wait_for_manual_captcha(self, page) -> None:
        signs = [
            "iframe[src*='captcha']",
            "iframe[src*='recaptcha']",
            "iframe[src*='hcaptcha']",
            ".g-recaptcha",
            "#captcha",
            "input[name*='captcha']",
            "img[src*='captcha']",
            "div[class*='captcha']",
            "div[class*='Captcha']",
        ]
        found = False
        for sel in signs:
            try:
                loc = page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible(timeout=1_000):
                    found = True
                    break
            except Exception:
                pass

        if found:
            timeout = getattr(config, "MANUAL_CAPTCHA_TIMEOUT_SEC", 180)
            print(
                "\n⚠️  Обнаружена CAPTCHA. Пройдите её вручную "
                "в открытом браузере и нажмите Enter в консоли. "
                f"Рекомендуемое время: до {timeout} сек."
            )
            try:
                input("Продолжить после CAPTCHA: ")
            except Exception:
                time.sleep(min(timeout, 30))

    def _new_secondary_browser(self, browser_type: str = "firefox",
                                user_agent: str | None = None,
                                extra_headers: dict | None = None):
        pw = getattr(config, "PLAYWRIGHT", None)
        if pw is None:
            raise RuntimeError(
                "config.PLAYWRIGHT не задан. Убедитесь, что main.py "
                "выполняет `config.PLAYWRIGHT = p` внутри "
                "`with sync_playwright() as p:` до запуска чекеров."
            )

        bt = getattr(pw, browser_type)
        browser = bt.launch(headless=config.HEADLESS)
        ctx = browser.new_context(
            viewport=config.VIEWPORT,
            user_agent=user_agent or config.USER_AGENT,
        )




        ctx.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )

        if extra_headers:
            ctx.set_extra_http_headers(extra_headers)

        page = ctx.new_page()
        page.on("dialog", lambda d: d.dismiss())
        return browser, page

    def _fill_inn(self, page: Page, inn: str, selectors: list) -> None:
        for sel in selectors:
            try:
                loc = page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible(timeout=1_500):
                    loc.first.click()
                    loc.first.fill(inn)
                    return
            except Exception:
                pass
        raise RuntimeError(f"Поле ИНН не найдено: {selectors}")

    def _submit(self, page: Page, field_locator, submit_selectors: list) -> None:
        for sel in submit_selectors:
            try:
                btn = page.locator(sel)
                if btn.count() > 0 and btn.first.is_visible(timeout=1_500):
                    btn.first.click()
                    return
            except Exception:
                pass
        try:
            field_locator.press("Enter")
        except Exception:
            pass



def _base_click_any(self, page, selectors, timeout=1500):
    for sel in selectors:
        try:
            loc = page.locator(sel)
            if loc.count() > 0:
                el = loc.first
                try:
                    el.scroll_into_view_if_needed(timeout=timeout)
                except Exception:
                    pass
                try:
                    if el.is_visible(timeout=timeout):
                        el.click(timeout=timeout)
                        return True
                except Exception:
                    pass
                try:
                    el.click(force=True, timeout=timeout)
                    return True
                except Exception:
                    pass
                try:
                    handle = el.element_handle(timeout=timeout)
                    if handle:
                        page.evaluate("el => el.click()", handle)
                        return True
                except Exception:
                    pass
        except Exception:
            pass
    return False


def _base_submit_search(self, page, field=None, extra_selectors=None, wait_ms=None):
    selectors = list(extra_selectors or []) + [
        "button[type='submit']",
        "input[type='submit']",
        "button:has-text('Найти')",
        "button:has-text('Поиск')",
        "input[value*='Найти']",
        "input[value*='Поиск']",
        "button[class*='search']",
        "[class*='search'] button",
    ]
    clicked = self._click_any(page, selectors)
    if not clicked and field is not None:
        try:
            field.press("Enter")
            clicked = True
        except Exception:
            pass
    if wait_ms is None:
        wait_ms = getattr(config, "TIMEOUT_LONG", 10000)
    page.wait_for_timeout(wait_ms)
    return clicked


BaseChecker._click_any = _base_click_any
BaseChecker._submit_search = _base_submit_search


def _base_close_yandex_browser_popup(self, page):
    popup_texts = [
        "Установить Яндекс Браузер",
        "установить Яндекс Браузер",
        "Яндекс Браузер",
        "Браузер",
    ]

    def popup_visible():
        for text in popup_texts:
            try:
                loc = page.get_by_text(text, exact=False)
                if loc.count() > 0 and loc.first.is_visible(timeout=500):
                    return loc.first
            except Exception:
                pass
        return None

    for _ in range(4):
        text_loc = popup_visible()
        if text_loc is None:
            return True

        close_selectors = [
            "button[aria-label='Закрыть']",
            "button[aria-label='Close']",
            "[aria-label='Закрыть']",
            "[aria-label='Close']",
            "button[title='Закрыть']",
            "[title='Закрыть']",
            "button:has-text('×')",
            "button:has-text('✕')",
            "button:has-text('Закрыть')",
            "[class*='close']",
            "[class*='Close']",
            "[data-testid*='close']",
            "[data-zone-name*='close']",
            "svg[class*='close']",
        ]
        if self._click_any(page, close_selectors, timeout=700):
            page.wait_for_timeout(800)
            continue

        try:
            box = text_loc.bounding_box(timeout=1_000)
            if box:
                for dx, dy in ((260, -22), (320, -28), (360, 0), (420, -36)):
                    page.mouse.click(box["x"] + box["width"] + dx, max(8, box["y"] + dy))
                    page.wait_for_timeout(400)
                    if popup_visible() is None:
                        return True
        except Exception:
            pass

        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(700)
            if popup_visible() is None:
                return True
        except Exception:
            pass

        try:
            removed = page.evaluate("""
                () => {
                    const re = new RegExp('Установить\\s+Яндекс\\s+Браузер|Яндекс\\s+Браузер', 'i');
                    const nodes = Array.from(document.querySelectorAll('div, section, aside, dialog, iframe'));
                    let count = 0;
                    for (const el of nodes) {
                        const text = el.innerText || el.textContent || '';
                        if (re.test(text)) {
                            el.remove();
                            count++;
                        }
                    }
                    document.body.style.overflow = 'auto';
                    return count;
                }
            """)
            page.wait_for_timeout(500)
            if removed or popup_visible() is None:
                return True
        except Exception:
            pass

    return popup_visible() is None


BaseChecker._close_yandex_browser_popup = _base_close_yandex_browser_popup
