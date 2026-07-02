import argparse
import os
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright

import config
from checkers import ALL_CHECKERS
from report import create_word_report


CHECKER_ALIASES = {
    "vestnik":      0,
    "pb_nalog":     1,
    "bo":           2,
    "rmsp":         3,
    "rnp":          4,
    "zakupki_1928": 5,
    "fedresurs":    6,
    "bankrot":      7,
    "kad":          8,
    "fssp":         9,
    "minjust":      10,
    "official":     11,
    "company_media":12,
    "founders":     13,
    "person_pb":    14,
    "passport":     15,
    "sudact":       16,
    "rso":          17,
    "person_media": 18,
}

def parse_args():
    parser = argparse.ArgumentParser(
        description="Автоматическая проверка контрагента(ов) по открытым реестрам"
    )
    parser.add_argument("--config", default=config.DEFAULT_CONFIG_PATH,
                        help="Путь к JSON-файлу конфигурации (по умолчанию config.json)")
    parser.add_argument("--inn", default=None,
                        help="Проверить только одну компанию с этим ИНН из списка companies")
    parser.add_argument("--all", action="store_true",
                        help="Проверить все компании из списка companies "
                             "(по умолчанию проверяется только первая)")
    parser.add_argument("--headless", action="store_true",
                        help="Запустить браузер без GUI")
    parser.add_argument("--only", nargs="+", choices=list(CHECKER_ALIASES.keys()),
                        metavar="CHECKER",
                        help=f"Запустить только указанные чекеры: {list(CHECKER_ALIASES)}")
    return parser.parse_args()



def run_checks(inn: str, headless: bool, checkers) -> list[tuple]:
    results = []

    with sync_playwright() as p:
        print("🚀  Запуск браузера…")

        config.PLAYWRIGHT = p

        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(
            viewport=config.VIEWPORT,
            user_agent=config.USER_AGENT,

            geolocation=None,
            permissions=[],
        )


        ctx.grant_permissions([])

        page = ctx.new_page()

        page.on("dialog", lambda d: d.dismiss())

        total = len(checkers)
        for i, checker in enumerate(checkers, start=1):
            print(f"\n📸  [{i}/{total}] {checker.TITLE[:60]}…")
            result = checker.run(page, inn)
            results.append(result)

        browser.close()

    return results



def process_company(company: dict, headless: bool, checkers) -> str:
    config.set_active_company(company)
    inn = config.INN

    print("=" * 60)
    print(f"  ПРОВЕРКА КОНТРАГЕНТА: {config.COMPANY_NAME or '(без названия)'} (ИНН {inn})")
    print(f"  Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"  Чекеров: {len(checkers)}")
    print("=" * 60)

    screenshots_data = run_checks(inn, headless, checkers)

    print("\n📄  Формируем Word-отчёт…")
    report_file = create_word_report(
        company_name=config.COMPANY_NAME,
        inn=inn,
        executor_name=config.EXECUTOR_NAME,
        address=config.ADDRESS,
        screenshots_data=screenshots_data,
    )

    if sys.platform == "win32":
        os.startfile(report_file)

    ok  = sum(1 for _, path, _ in screenshots_data if path)
    bad = len(screenshots_data) - ok
    print(f"\n✅  Успешно: {ok}/{len(screenshots_data)}   ❌  Ошибок: {bad}")
    print(f"📄  Отчёт сохранён: {report_file}\n")
    return report_file



def main():
    args = parse_args()




    if args.config != config.DEFAULT_CONFIG_PATH or not config.COMPANIES:
        try:
            config.load(args.config)
        except (FileNotFoundError, ValueError) as e:
            print(f"❌  {e}")
            sys.exit(1)

    if args.only:
        indices = [CHECKER_ALIASES[name] for name in args.only]
        checkers = [ALL_CHECKERS[i] for i in sorted(set(indices))]
    else:
        checkers = ALL_CHECKERS

    headless = args.headless or config.HEADLESS


    if args.inn:
        company = config.find_company(args.inn)
        if not company:
            print(f"❌  Компания с ИНН {args.inn} не найдена в {config.config_path()}")
            sys.exit(1)
        companies_to_run = [company]
    elif args.all:
        companies_to_run = config.COMPANIES
    else:
        companies_to_run = [config.COMPANIES[0]]

    print(f"📋  Конфигурация: {config.config_path()}")
    print(f"📋  Компаний к проверке: {len(companies_to_run)}\n")

    reports = []
    for i, company in enumerate(companies_to_run, start=1):
        if len(companies_to_run) > 1:
            print(f"\n### Компания {i}/{len(companies_to_run)} ###")
        reports.append(process_company(company, headless, checkers))

    print("\n" + "=" * 60)
    print(f"  ГОТОВО. Сформировано отчётов: {len(reports)}")
    for r in reports:
        print(f"   • {r}")
    print("=" * 60)


if __name__ == "__main__":
    main()
