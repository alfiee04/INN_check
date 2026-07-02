from urllib.parse import quote_plus
from playwright.sync_api import Page
from .base import BaseChecker
import config


class CompanyMediaSearchChecker(BaseChecker):
    TITLE = "Иные источники, в том числе СМИ: поиск по наименованию и ИНН"
    URL = "https://ya.ru/search/?text="

    def check(self, page: Page, inn: str) -> str:
        q = quote_plus(f"{config.COMPANY_NAME} {inn} негатив суд СМИ")
        self._goto(page, self.URL + q, wait_until="domcontentloaded")
        page.wait_for_timeout(3_000)
        self._close_yandex_browser_popup(page)
        self._close_modal_accept(page)
        page.wait_for_timeout(config.TIMEOUT_LONG)
        return self._screenshot(page, "14_company_media_search.png")


class PersonMediaSearchChecker(BaseChecker):
    TITLE = "Иные источники, в том числе СМИ: поиск по ФИО и ИНН"
    URL = "https://ya.ru/search/?text="

    def check(self, page: Page, inn: str) -> str:
        fio = getattr(config, "PERSON_FIO", "").strip() or getattr(config, "DIRECTOR_FIO", "").strip()
        pin = getattr(config, "PERSON_INN", "").strip()
        company_name = getattr(config, "COMPANY_NAME", "").strip()
        company_inn = (inn or getattr(config, "INN", "")).strip()
        query = f"{fio} {pin} {company_name} {company_inn} негатив суд СМИ".strip()
        if not query:
            query = f"{config.COMPANY_NAME} {inn} руководитель учредитель СМИ"
        self._goto(page, self.URL + quote_plus(query), wait_until="domcontentloaded")
        page.wait_for_timeout(3_000)
        self._close_yandex_browser_popup(page)
        self._close_modal_accept(page)
        page.wait_for_timeout(config.TIMEOUT_LONG)
        return self._screenshot(page, "20_person_media_search.png")
