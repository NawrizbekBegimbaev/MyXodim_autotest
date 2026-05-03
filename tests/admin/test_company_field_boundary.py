"""UC-4.1 boundary по полям формы создания компании.

Все тесты ожидают что форма НЕ ушла в success-state. Для невалидных
вариантов это либо 400/409 от бэка (BUG-006: фронт не показывает toast),
либо submit заблокирован фронтовой валидацией.
"""

from __future__ import annotations

import secrets

import allure
import pytest
from playwright.sync_api import BrowserContext, expect

from config.settings import Settings
from data.constants import E2E_ORG_PREFIX
from pages.admin.create_company_page import CreateCompanyPage


def _rd(n: int) -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(n))


def _valid_pinfl() -> str:
    return f"{secrets.randbelow(6) + 1}{_rd(13)}"


def _fresh_data() -> dict[str, str]:
    suffix = _rd(6)
    return {
        "name": f"{E2E_ORG_PREFIX} bnd-{suffix}",
        "slug": f"e2e-bnd-{suffix}",
        "inn": _rd(9),
        "first_name": "Тест",
        "last_name": "Тестов",
        "phone_local": f"905{_rd(7)}",
        "pinfl": _valid_pinfl(),
    }


def _open_with(
    ctx: BrowserContext, settings: Settings, overrides: dict[str, str]
) -> CreateCompanyPage:
    page = ctx.new_page()
    data = {**_fresh_data(), **overrides}
    create = CreateCompanyPage(page).goto(settings.admin_url)
    create.fill_company(name=data["name"], slug=data["slug"], inn=data["inn"]).fill_admin(
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone_local=data["phone_local"],
        pinfl=data["pinfl"],
    )
    return create


def _expect_no_success(create: CreateCompanyPage, settings: Settings) -> None:
    """Submit + проверка что success-heading НЕ появился, форма остаётся."""
    create.submit()
    page = create.page
    # form heading должен оставаться, success-heading не появляется (expect.not_to_be_visible ретраится)
    expect(create.page_heading).to_be_visible(timeout=settings.expect_timeout)
    expect(page.get_by_role("heading", name="Компания создана", level=5)).not_to_be_visible()


# ---------- Название компании ----------


@pytest.mark.negative
@pytest.mark.parametrize(
    "name",
    [
        pytest.param("", id="empty"),
        pytest.param("   ", id="only-spaces"),
        pytest.param("a", id="single-char"),
        pytest.param("X" * 500, id="extremely-long"),
    ],
)
@allure.title("Company name boundary: '{name}' → форма не уходит в success")
def test_company_name_boundary(
    super_admin_context: BrowserContext, settings: Settings, name: str
) -> None:
    create = _open_with(super_admin_context, settings, overrides={"name": name})
    _expect_no_success(create, settings)


@pytest.mark.negative
@pytest.mark.parametrize(
    "name",
    [
        pytest.param("<script>alert(1)</script>", id="xss-payload"),
        pytest.param("'; DROP TABLE tenants; --", id="sqli-payload"),
    ],
)
@allure.title("Company name security: '{name}' принимается, payload не выполняется")
def test_company_name_security_payload_safe(
    super_admin_context: BrowserContext, settings: Settings, name: str
) -> None:
    """Бэк/фронт принимают строку как обычный текст. Главное — payload
    не должен выполниться (нет alert dialog, нет drop table).
    """
    from playwright.sync_api import Dialog

    from pages.admin.create_company_page import CompanyCreatedView

    page = super_admin_context.new_page()
    dialogs: list[str] = []

    def on_dialog(d: Dialog) -> None:
        dialogs.append(d.message)
        d.dismiss()

    page.on("dialog", on_dialog)

    data = {**_fresh_data(), "name": name}
    create = CreateCompanyPage(page).goto(settings.admin_url)
    create.fill_company(name=data["name"], slug=data["slug"], inn=data["inn"]).fill_admin(
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone_local=data["phone_local"],
        pinfl=data["pinfl"],
    )
    create.submit()
    expect(CompanyCreatedView(page).heading).to_be_visible(timeout=settings.nav_timeout)
    assert dialogs == [], f"XSS/SQLi payload вызвал dialog: {dialogs}"


# ---------- Slug ----------


@pytest.mark.negative
@pytest.mark.parametrize(
    "slug",
    [
        pytest.param("", id="empty"),
        pytest.param("e2e bnd 123", id="spaces"),
        pytest.param("E2E-BND-123", id="uppercase"),
        pytest.param("е2е-кириллица", id="cyrillic"),
        pytest.param("---", id="only-hyphens"),
        pytest.param("-leading-hyphen", id="leading-hyphen"),
        pytest.param("trailing-hyphen-", id="trailing-hyphen"),
        pytest.param("with_underscore", id="underscore"),
        pytest.param("with.dot", id="dot"),
        pytest.param("a", id="single-char"),
        pytest.param("X" * 200, id="too-long"),
    ],
)
@allure.title("Company slug boundary: '{slug}' → форма не уходит в success")
def test_company_slug_boundary(
    super_admin_context: BrowserContext, settings: Settings, slug: str
) -> None:
    create = _open_with(super_admin_context, settings, overrides={"slug": slug})
    _expect_no_success(create, settings)


# ---------- ИНН ----------


@pytest.mark.negative
@pytest.mark.parametrize(
    "inn",
    [
        pytest.param("0123456789", id="too-long-10"),
        pytest.param("12345678901234", id="too-long-14"),
        pytest.param("000000000", id="all-zeros"),
        pytest.param("999999999", id="all-nines"),
        pytest.param("12 34 567", id="spaces-inside"),
        pytest.param("12-345-67", id="hyphens-inside"),
        pytest.param("-123456789", id="negative"),
        pytest.param("123.45678", id="float"),
        pytest.param("١٢٣٤٥٦٧٨٩", id="arabic-digits"),
    ],
)
@allure.title("Company ИНН boundary: '{inn}' → форма не уходит в success")
def test_company_inn_boundary(
    super_admin_context: BrowserContext, settings: Settings, inn: str
) -> None:
    create = _open_with(super_admin_context, settings, overrides={"inn": inn})
    _expect_no_success(create, settings)


# ---------- Имя/Фамилия admin ----------


@pytest.mark.negative
@pytest.mark.parametrize(
    "first_name",
    [
        pytest.param("", id="empty"),
        pytest.param("   ", id="only-spaces"),
        pytest.param("X" * 500, id="too-long"),
        pytest.param("Имя!@#", id="special-chars"),
    ],
)
@allure.title("Company admin Имя boundary: '{first_name}' → форма не уходит в success")
def test_company_admin_first_name_boundary(
    super_admin_context: BrowserContext, settings: Settings, first_name: str
) -> None:
    create = _open_with(super_admin_context, settings, overrides={"first_name": first_name})
    _expect_no_success(create, settings)


@pytest.mark.negative
@pytest.mark.parametrize(
    "last_name",
    [
        pytest.param("Фамилия123", id="digits"),
        pytest.param("", id="empty"),
        pytest.param("   ", id="only-spaces"),
        pytest.param("X" * 500, id="too-long"),
        pytest.param("Фамилия!@#", id="special-chars"),
    ],
)
@allure.title("Company admin Фамилия boundary: '{last_name}' → форма не уходит в success")
def test_company_admin_last_name_boundary(
    super_admin_context: BrowserContext, settings: Settings, last_name: str
) -> None:
    create = _open_with(super_admin_context, settings, overrides={"last_name": last_name})
    _expect_no_success(create, settings)


# ---------- Phone admin (на форме создания) ----------


@pytest.mark.negative
@pytest.mark.parametrize(
    "phone_local",
    [
        pytest.param("12345", id="too-short"),
        pytest.param("905123456789", id="too-long"),
        pytest.param("905 123 4567", id="spaces"),
        pytest.param("905-123-4567", id="hyphens"),
        pytest.param("abcdefg12", id="letters"),
        pytest.param("", id="empty"),
        pytest.param("000000000", id="all-zeros-9"),
    ],
)
@allure.title("Company admin Телефон boundary: '{phone_local}' → форма не уходит в success")
def test_company_admin_phone_boundary(
    super_admin_context: BrowserContext, settings: Settings, phone_local: str
) -> None:
    create = _open_with(super_admin_context, settings, overrides={"phone_local": phone_local})
    _expect_no_success(create, settings)


# ---------- ПИНФЛ boundary (доп.) ----------


@pytest.mark.negative
@pytest.mark.parametrize(
    "pinfl",
    [
        pytest.param("1" * 13, id="13-digits"),
        pytest.param("1" * 15, id="15-digits"),
        pytest.param("1abcdefghijklm", id="letters-mixed"),
        pytest.param("1" + "0" * 13, id="leading-1-then-zeros"),
        pytest.param("1 " + "0" * 12, id="space-inside"),
    ],
)
@allure.title("Company admin ПИНФЛ boundary: '{pinfl}' → форма не уходит в success")
def test_company_admin_pinfl_boundary(
    super_admin_context: BrowserContext, settings: Settings, pinfl: str
) -> None:
    create = _open_with(super_admin_context, settings, overrides={"pinfl": pinfl})
    _expect_no_success(create, settings)


# ---------- Positive boundary (валидные пограничные) ----------


@pytest.mark.positive
@pytest.mark.parametrize(
    "first_name,last_name",
    [
        pytest.param("Анна-Мария", "Иванова-Петрова", id="hyphen"),
        pytest.param("О'Брайен", "О'Коннор", id="apostrophe"),
        pytest.param("Иван Иванович", "Тестов Тестович", id="multi-word"),
    ],
)
@allure.title("Company admin Имя/Фамилия positive boundary: '{first_name}' / '{last_name}'")
def test_company_admin_name_positive_boundary(
    super_admin_context: BrowserContext,
    settings: Settings,
    first_name: str,
    last_name: str,
) -> None:
    """По UI-валидации разрешены только буквы, пробелы, дефис и апостроф —
    проверяем что эти варианты приняты (форма уходит в success).
    """
    from pages.admin.create_company_page import CompanyCreatedView

    page = super_admin_context.new_page()
    data = {**_fresh_data(), "first_name": first_name, "last_name": last_name}
    create = CreateCompanyPage(page).goto(settings.admin_url)
    create.fill_company(name=data["name"], slug=data["slug"], inn=data["inn"]).fill_admin(
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone_local=data["phone_local"],
        pinfl=data["pinfl"],
    )
    create.submit()
    expect(CompanyCreatedView(page).heading).to_be_visible(timeout=settings.nav_timeout)
