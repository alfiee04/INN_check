from playwright.sync_api import Page
from .transparent_biz import TransparentBizChecker
import config


class PersonTransparentBizChecker(TransparentBizChecker):
    TITLE = (
        "Участие в нескольких юридических лицах, дисквалифицированное лицо, "
        "ограничения участия в ЮЛ (https://pb.nalog.ru/search.html)"
    )

    def check(self, page: Page, inn: str) -> str:
        person_inn = getattr(config, "PERSON_INN", "").strip()
        if not person_inn:
            print("  ⚠️  PERSON_INN не задан — будет открыта страница Прозрачного бизнеса для ручного ввода")
            person_inn = inn
        path = super().check(page, person_inn)

        return path
