"""Кнопки/элементы Admin UI которые не покрыты в основных файлах:
- "Назад" / "Отмена" / "Вернуться к списку компаний" на форме создания
- Click по строке компании → /tenants/{id} (detail page)
- Detail page: имя, slug, ключ интеграции, статус, table пользователей, кнопки
- Records per page combobox (10/25/50/100)
- "Все" в Недавних компаниях на дашборде
- User menu кнопка существует
- Edge cases ввода: длинный paste, drag&drop
"""

from __future__ import annotations

import re
import secrets
from collections.abc import Iterator

import allure
import pytest
from playwright.sync_api import BrowserContext, Page, expect

from config.settings import Settings
from data.constants import E2E_ORG_PREFIX
from pages.admin.create_company_page import CompanyCreatedView, CreateCompanyPage
from pages.admin.organizations_page import OrganizationsPage


def _rd(n: int) -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(n))


def _valid_pinfl() -> str:
    return f"{secrets.randbelow(6) + 1}{_rd(13)}"


def _fresh_data() -> dict[str, str]:
    suffix = _rd(6)
    return {
        "name": f"{E2E_ORG_PREFIX} btn-{suffix}",
        "slug": f"e2e-btn-{suffix}",
        "inn": _rd(9),
        "first_name": "Тест",
        "last_name": "Тестов",
        "phone_local": f"905{_rd(7)}",
        "pinfl": _valid_pinfl(),
    }


def _open_list(ctx: BrowserContext, settings: Settings) -> OrganizationsPage:
    page = ctx.new_page()
    page.goto(f"{settings.admin_url}/dashboard", wait_until="networkidle")
    page.goto(f"{settings.admin_url}/tenants", wait_until="networkidle")
    orgs = OrganizationsPage(page)
    expect(orgs.heading).to_be_visible(timeout=settings.nav_timeout)
    expect(orgs.table.get_by_role("row").nth(1)).to_be_visible(timeout=settings.nav_timeout)
    return orgs


# ---------- Form buttons ----------


@pytest.mark.positive
@allure.title("Форма /tenants/new: кнопка 'Назад' редиректит на /tenants")
def test_form_back_button_redirects_to_tenants_list(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    CreateCompanyPage(page).goto(settings.admin_url)
    page.get_by_role("button", name="Назад").click()
    expect(page).to_have_url(re.compile(r"/tenants(\?|$)"), timeout=settings.nav_timeout)


@pytest.mark.positive
@allure.title("Форма /tenants/new: кнопка 'Отмена' не создаёт компанию")
def test_form_cancel_button_does_not_create(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    data = _fresh_data()
    create = CreateCompanyPage(page).goto(settings.admin_url)
    create.fill_company(name=data["name"], slug=data["slug"], inn=data["inn"]).fill_admin(
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone_local=data["phone_local"],
        pinfl=data["pinfl"],
    )
    page.get_by_role("button", name="Отмена").click()
    # success heading НЕ появился; expect.not_to_be_visible имеет встроенный retry
    expect(page.get_by_role("heading", name="Компания создана", level=5)).not_to_be_visible()


@pytest.mark.positive
@allure.title("Success-state: 'Вернуться к списку компаний' редиректит на /tenants")
def test_success_back_to_list_button_redirects(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    data = _fresh_data()
    create = CreateCompanyPage(page).goto(settings.admin_url)
    create.fill_company(name=data["name"], slug=data["slug"], inn=data["inn"]).fill_admin(
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone_local=data["phone_local"],
        pinfl=data["pinfl"],
    ).submit()
    success = CompanyCreatedView(page)
    expect(success.heading).to_be_visible(timeout=settings.nav_timeout)

    success.click_back()
    expect(page).to_have_url(re.compile(r"/tenants(\?|$)"), timeout=settings.nav_timeout)


# ---------- List interactions ----------


@pytest.mark.positive
@allure.title("Click по строке компании → /tenants/{uuid}")
def test_click_company_row_opens_detail_page(
    super_admin_live_context: BrowserContext, settings: Settings
) -> None:
    orgs = _open_list(super_admin_live_context, settings)
    orgs.table.get_by_role("row").nth(1).click()
    expect(orgs.page).to_have_url(
        re.compile(r"/tenants/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"),
        timeout=settings.nav_timeout,
    )


@pytest.mark.positive
@allure.title("Records per page combobox: опции 10/25/50/100")
def test_records_per_page_combobox_has_expected_options(
    super_admin_live_context: BrowserContext, settings: Settings
) -> None:
    orgs = _open_list(super_admin_live_context, settings)
    combo = orgs.page.get_by_role("combobox").last
    combo.click()
    listbox = orgs.page.get_by_role("listbox")
    expect(listbox).to_be_visible(timeout=settings.expect_timeout)
    for opt in ["10", "25", "50", "100"]:
        expect(listbox.get_by_role("option", name=opt, exact=True)).to_be_visible()


@pytest.mark.positive
@allure.title("Records per page: смена на 50 не ломает страницу")
def test_records_per_page_change_to_50(
    super_admin_live_context: BrowserContext, settings: Settings
) -> None:
    orgs = _open_list(super_admin_live_context, settings)
    page = orgs.page
    combo = page.get_by_role("combobox").last
    combo.click()
    listbox = page.get_by_role("listbox")
    expect(listbox).to_be_visible(timeout=settings.expect_timeout)
    # Ждём ответ от бэка с новым размером страницы — на /tenants?size=50
    with page.expect_response(
        lambda r: "/tenants" in r.url and r.request.method == "GET",
        timeout=settings.nav_timeout,
    ):
        listbox.get_by_role("option", name="50", exact=True).click()
    expect(orgs.heading).to_be_visible()


@pytest.mark.positive
@allure.title("Дашборд: кнопка 'Все' редиректит на /tenants")
def test_dashboard_all_recent_button_navigates_to_tenants(
    super_admin_live_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_live_context.new_page()
    page.goto(f"{settings.admin_url}/dashboard", wait_until="networkidle")
    btn_all = page.get_by_role("button", name="Все")
    expect(btn_all).to_be_visible(timeout=settings.expect_timeout)
    btn_all.click()
    expect(page).to_have_url(re.compile(r"/tenants(\?|$)"), timeout=settings.nav_timeout)


# ---------- Detail page (/tenants/{uuid}) ----------


@pytest.fixture
def detail_page(
    super_admin_live_context: BrowserContext,
    settings: Settings,
    anchor_company: dict[str, str],
) -> Iterator[tuple[Page, dict[str, str]]]:
    """Открывает detail page anchor_company через клик по row."""
    orgs = _open_list(super_admin_live_context, settings)
    orgs.search(anchor_company["slug"])
    row = orgs.row_by_name(anchor_company["name"])
    expect(row).to_be_visible(timeout=settings.nav_timeout)
    row.click()
    page = orgs.page
    expect(page).to_have_url(
        re.compile(r"/tenants/[0-9a-f-]{36}"), timeout=settings.nav_timeout
    )
    # detail-страница рендерится после URL match — ждём ключевой heading
    expect(page.get_by_role("heading", name=anchor_company["name"], level=5)).to_be_visible(
        timeout=settings.nav_timeout
    )
    yield page, anchor_company


@pytest.mark.positive
@allure.title("Detail: имя компании в heading + slug в paragraph")
def test_company_detail_shows_name_and_slug(
    detail_page: tuple[Page, dict[str, str]], settings: Settings
) -> None:
    page, data = detail_page
    expect(page.get_by_role("heading", name=data["name"], level=5)).to_be_visible(
        timeout=settings.expect_timeout
    )
    expect(page.get_by_text(data["slug"]).first).to_be_visible()


@pytest.mark.positive
@allure.title("Detail: ключ интеграции `bh_live_<32hex>` показан")
def test_company_detail_shows_integration_key(
    detail_page: tuple[Page, dict[str, str]],
) -> None:
    page, _ = detail_page
    expect(page.get_by_text(re.compile(r"bh_live_[a-f0-9]{32}"))).to_be_visible()


@pytest.mark.positive
@allure.title("Detail: статус 'Активна' и счётчик пользователей")
def test_company_detail_shows_status_and_users_count(
    detail_page: tuple[Page, dict[str, str]],
) -> None:
    page, _ = detail_page
    expect(page.get_by_text("Активна").first).to_be_visible()
    expect(page.get_by_role("heading", level=6).filter(has_text=re.compile(r"Пользователи"))).to_be_visible()


@pytest.mark.positive
@allure.title("Detail: таблица пользователей с колонками")
def test_company_detail_shows_users_table(
    detail_page: tuple[Page, dict[str, str]],
) -> None:
    page, _ = detail_page
    table = page.get_by_role("table").last
    for col in ["Пользователь", "Телефон", "Роль", "Статус"]:
        expect(table.get_by_role("columnheader", name=col)).to_be_visible()
    # admin row (тот что мы создали при анкоре): Якорь Тестовый
    expect(table.get_by_role("row").filter(has_text="Якорь Тестовый")).to_be_visible()


@pytest.mark.positive
@allure.title("Detail: кнопки 'Редактировать' и 'Отключить'")
def test_company_detail_has_edit_and_disable_buttons(
    detail_page: tuple[Page, dict[str, str]],
) -> None:
    page, _ = detail_page
    expect(page.get_by_role("button", name="Редактировать")).to_be_visible()
    expect(page.get_by_role("button", name="Отключить")).to_be_visible()


@pytest.mark.positive
@allure.title("Detail: кнопка 'Компании' (breadcrumb-back) редиректит на /tenants")
def test_company_detail_back_to_companies_button(
    detail_page: tuple[Page, dict[str, str]], settings: Settings
) -> None:
    page, _ = detail_page
    page.get_by_role("button", name="Компании").click()
    expect(page).to_have_url(re.compile(r"/tenants(\?|$)"), timeout=settings.nav_timeout)


# ---------- Field input edge cases ----------


@pytest.mark.negative
@allure.title("Edge: длинный paste (5000 символов) в поле Название не валит фронт")
def test_company_form_long_paste_does_not_crash(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    create = CreateCompanyPage(page).goto(settings.admin_url)
    expect(create.page_heading).to_be_visible(timeout=settings.expect_timeout)
    name_input = page.get_by_role("textbox", name="Название компании")
    name_input.fill("X" * 5000)
    # Страница ещё жива — heading "Новая компания" виден (expect ретраится)
    expect(create.page_heading).to_be_visible()


@pytest.mark.negative
@allure.title("Edge: drag&drop текста в поле — поле принимает или игнорирует, фронт не валится")
def test_company_form_drag_drop_does_not_crash(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    create = CreateCompanyPage(page).goto(settings.admin_url)
    expect(create.page_heading).to_be_visible(timeout=settings.expect_timeout)
    name_input = page.get_by_role("textbox", name="Название компании")
    slug_input = page.get_by_role("textbox", name="Slug")
    name_input.fill("Source name")
    # Drag из name в slug — поведение браузера зависит, тест проверяет что фронт не падает
    name_input.drag_to(slug_input)
    expect(create.page_heading).to_be_visible()


@pytest.mark.negative
@allure.title("Edge: вставка emoji в название → форма работает, страница не падает")
def test_company_form_emoji_in_name(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    create = CreateCompanyPage(page).goto(settings.admin_url)
    name_input = page.get_by_role("textbox", name="Название компании")
    name_input.fill("Test 🏢 Company 🇺🇿 ✓")
    expect(create.page_heading).to_be_visible()


@pytest.mark.negative
@allure.title("Edge: RTL-строка в поле Название не валит layout")
def test_company_form_rtl_text_in_name(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    create = CreateCompanyPage(page).goto(settings.admin_url)
    name_input = page.get_by_role("textbox", name="Название компании")
    name_input.fill("شركة اختبار")  # арабский — справа налево
    expect(create.page_heading).to_be_visible()
