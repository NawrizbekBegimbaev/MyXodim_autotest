"""Sanity cases 8-27 — Client UI pages open/load for the ADMINISTRATOR.

Each case = navigate to the route and assert it rendered (heading visible, or
the app shell for heading-less pages), plus the create control where the report
expects "создание работает".
"""

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.client.app_page import ClientAppPage

pytestmark = [pytest.mark.sanity, pytest.mark.client]

# (case_no, section, route, heading | None, create_button | None)
CASES = [
    (8, "Дашборд", "/home", "Добро пожаловать", None),
    (9, "Расчётный лист", "/payslip", "Расчётные листы", None),
    (10, "График работы", "/work-schedule", None, None),
    (11, "Отпуск", "/vacation", None, None),
    (12, "Задание на согласование", "/approval-jobs", "Задание на согласования документов", None),
    (13, "Задачи исполнителей", "/executor-tasks", "Задачи исполнителей", None),
    (14, "Документ для согласования", "/approval-documents", "Документ для согласования", "Создать"),
    (15, "Виды документов", "/document-types", "Виды документов для согласования", "Создать"),
    (16, "Группы видов документов", "/document-groups", "Группы видов документов", "Создать"),
    (17, "Маршрут для согласования", "/routes", "Шаблоны маршрутов", "Создать маршрут"),
    (18, "Роли для согласования", "/approval-roles", "Роли для согласований", "Создать"),
    (19, "Роли сотрудника", "/employee-roles", "Роли сотрудников в организации", "Создать"),
    (20, "Сотрудники", "/members", "Сотрудники", "Добавить сотрудника"),
    (21, "Должности", "/positions", "Должности", "Добавить должность"),
    (22, "Организация", "/organization", "Настройки организации", None),
    (23, "Подразделение", "/departments", "Подразделения", "Добавить подразделение"),
    (24, "Физические лица", "/persons", "Физические лица", "Добавить"),
    (25, "График работы (HR)", "/work-schedules", "Графики работы", "Создать"),
    (26, "Зарплата", "/payslips", "Зарплата", None),
    (27, "Отпуск (HR)", "/vacation-balances", "Отпуск", None),
]


@pytest.mark.parametrize(
    "case_no,section,route,heading,create_btn",
    CASES,
    ids=[f"{c[0]:02d}-{c[1]}" for c in CASES],
)
def test_client_page_opens(
    admin_client_page: Page, cfg, case_no, section, route, heading, create_btn
) -> None:
    allure.dynamic.title(f"{case_no}. {section} — страница открывается")
    check = f"заголовок «{heading}»" if heading else "интерфейс приложения отрисован"
    create_line = f"\n4. Проверить наличие кнопки «{create_btn}»." if create_btn else ""
    allure.dynamic.description(
        f"**Цель:** убедиться, что раздел «{section}» открывается без ошибок под ролью "
        f"Администратор.\n\n"
        f"**Окружение:** stage, Client UI ({cfg.client_url}).\n"
        f"**Предусловие:** выполнен вход как Администратор созданной [SANITY]-компании.\n\n"
        f"**Шаги воспроизведения:**\n"
        f"1. Войти в Client UI по телефону + OTP как Администратор.\n"
        f"2. Перейти по адресу `{route}`.\n"
        f"3. Дождаться загрузки страницы и проверить, что {check}.{create_line}\n\n"
        f"**Ожидаемый результат:** страница `{route}` открывается, "
        f"{check}{', кнопка создания доступна' if create_btn else ''}."
    )

    with allure.step(f"Открыть раздел «{section}» ({route})"):
        app = ClientAppPage(admin_client_page, cfg.client_url).open(route)

    with allure.step(f"Проверить, что страница отрисовалась ({check})"):
        if heading is not None:
            expect(app.heading(heading)).to_be_visible()
        else:
            # Heading-less page (calendar/cards): assert the shell + route mounted.
            expect(app.shell).to_be_visible()
            expect(admin_client_page).to_have_url(_url(cfg.client_url, route))

    if create_btn is not None:
        with allure.step(f"Проверить наличие кнопки «{create_btn}»"):
            expect(app.button(create_btn)).to_be_visible()


def _url(base: str, route: str):
    import re

    return re.compile(re.escape(route))
