"""UC-4.1 negative-pack: создание компании в Admin UI.

BRD §4.5: уникальность ИНН/slug/телефона. Frontend-валидация ИНН/ПИНФЛ.

Все 4xx ответы бэка фронт сейчас игнорирует (BUG-006) — поэтому в тестах
проверяем что форма НЕ переходит в success-state, а не наличие error-toast.
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
        "name": f"{E2E_ORG_PREFIX} neg-{suffix}",
        "slug": f"e2e-neg-{suffix}",
        "inn": _rd(9),
        "first_name": "Тест",
        "last_name": "Тестов",
        "phone_local": f"905{_rd(7)}",
        "pinfl": _valid_pinfl(),
    }


def _open_form_filled(
    ctx: BrowserContext, settings: Settings, overrides: dict[str, str]
) -> tuple[CreateCompanyPage, dict[str, str]]:
    """Открывает форму, заполняет fresh-данные с применением overrides."""
    page = ctx.new_page()
    data = {**_fresh_data(), **overrides}
    create = CreateCompanyPage(page).goto(settings.admin_url)
    create.fill_company(name=data["name"], slug=data["slug"], inn=data["inn"]).fill_admin(
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone_local=data["phone_local"],
        pinfl=data["pinfl"],
    )
    return create, data


def _expect_form_stays(page_object: CreateCompanyPage, settings: Settings) -> None:
    """После submit форма должна остаться на /tenants/new (success-heading НЕ появился).

    Используем длительный wait — форма SPA может не рендерить ошибку моментально.
    """
    page = page_object.page
    page.wait_for_load_state("networkidle", timeout=settings.nav_timeout)
    expect(page_object.page_heading).to_be_visible(timeout=settings.expect_timeout)
    success_heading = page.get_by_role("heading", name="Компания создана", level=5)
    expect(success_heading).not_to_be_visible()


def _submit_and_assert_response(
    create: CreateCompanyPage,
    settings: Settings,
    expected_status: int,
    expected_code: str | None = None,
) -> None:
    """Submit формы + перехват POST /admin/tenants + ассерт на status и code.

    Network-assertion закрывает класс BUG-006: тесты раньше проверяли только
    "форма осталась", но если бэк начнёт пропускать дубль (200) — тест-провайдер
    бы заметил это только через UI, а UI молчит (BUG-006). Теперь explicit ассерт.
    """
    page = create.page
    with page.expect_response(
        lambda r: "/api/v1/admin/tenants" in r.url
        and r.request.method == "POST"
        and not r.url.endswith("/enable")
        and not r.url.endswith("/disable"),
        timeout=settings.nav_timeout,
    ) as resp_info:
        create.submit()
    resp = resp_info.value
    assert resp.status == expected_status, (
        f"Ожидали {expected_status} от POST /admin/tenants, "
        f"получили {resp.status}. Body: {resp.text()[:300]}"
    )
    if expected_code is not None:
        body = resp.json()
        assert body.get("code") == expected_code, (
            f"Ожидали code={expected_code!r}, получили {body.get('code')!r}. "
            f"Body: {body}"
        )


# ---------- Backend duplicate-checks (409) — фронт молчит из-за BUG-006 ----------


@pytest.mark.negative
@allure.title("UC-4.1 neg: дубль ИНН → 409 INN_EXISTS, форма остаётся")
def test_company_create_with_duplicate_inn_stays_on_form(
    super_admin_context: BrowserContext, settings: Settings, anchor_company: dict[str, str]
) -> None:
    create, _ = _open_form_filled(
        super_admin_context, settings, overrides={"inn": anchor_company["inn"]}
    )
    _submit_and_assert_response(create, settings, expected_status=409, expected_code="INN_EXISTS")
    _expect_form_stays(create, settings)


@pytest.mark.negative
@allure.title("UC-4.1 neg: дубль slug → 409 SLUG_EXISTS, форма остаётся")
def test_company_create_with_duplicate_slug_stays_on_form(
    super_admin_context: BrowserContext, settings: Settings, anchor_company: dict[str, str]
) -> None:
    create, _ = _open_form_filled(
        super_admin_context, settings, overrides={"slug": anchor_company["slug"]}
    )
    _submit_and_assert_response(create, settings, expected_status=409, expected_code="SLUG_EXISTS")
    _expect_form_stays(create, settings)


@pytest.mark.negative
@allure.title("UC-4.1 neg: дубль телефона админа → 409 PHONE_ADMIN_EXISTS, форма остаётся")
def test_company_create_with_duplicate_admin_phone_stays_on_form(
    super_admin_context: BrowserContext, settings: Settings, anchor_company: dict[str, str]
) -> None:
    create, _ = _open_form_filled(
        super_admin_context,
        settings,
        overrides={"phone_local": anchor_company["phone_local"]},
    )
    _submit_and_assert_response(
        create, settings, expected_status=409, expected_code="PHONE_ADMIN_EXISTS"
    )
    _expect_form_stays(create, settings)


@pytest.mark.negative
@allure.title("UC-4.1 neg: дубль ПИНФЛ → 409 PINFL_EXISTS, форма остаётся")
def test_company_create_with_duplicate_pinfl_stays_on_form(
    super_admin_context: BrowserContext, settings: Settings, anchor_company: dict[str, str]
) -> None:
    create, _ = _open_form_filled(
        super_admin_context, settings, overrides={"pinfl": anchor_company["pinfl"]}
    )
    _submit_and_assert_response(
        create, settings, expected_status=409, expected_code="PINFL_EXISTS"
    )
    _expect_form_stays(create, settings)


@pytest.mark.negative
@allure.title("UC-4.1 neg: без ПИНФЛ → submit заблокирован фронт-валидацией")
def test_company_create_without_pinfl_stays_on_form(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    """После фикса BUG-002 ПИНФЛ — required на фронте: submit не отправляется
    вовсе (клиентская валидация). Поэтому network-assert не применим — POST
    не летит, ждём только что форма не уехала на success.
    """
    create, _ = _open_form_filled(super_admin_context, settings, overrides={"pinfl": ""})
    create.submit()
    _expect_form_stays(create, settings)


@pytest.mark.negative
@allure.title("UC-4.1 neg: ИНН буквами → 400, форма остаётся")
def test_company_create_with_letters_in_inn_stays_on_form(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    create, _ = _open_form_filled(super_admin_context, settings, overrides={"inn": "abcdefghi"})
    _submit_and_assert_response(create, settings, expected_status=400)
    _expect_form_stays(create, settings)


# ---------- Frontend validation (submit blocked, нет POST) ----------


@pytest.mark.negative
@allure.title("UC-4.1 neg: ИНН < 9 цифр → inline-ошибка, submit не отправлен")
def test_company_create_with_short_inn_shows_inline_error(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    create, _ = _open_form_filled(super_admin_context, settings, overrides={"inn": "12345"})
    create.submit()
    page = create.page
    expect(page.get_by_text("ИНН должен содержать 9 цифр")).to_be_visible(
        timeout=settings.expect_timeout
    )
    _expect_form_stays(create, settings)


@pytest.mark.negative
@allure.title("UC-4.1 neg: ПИНФЛ начинается не с 1-6 → inline-ошибка")
def test_company_create_with_invalid_pinfl_start_shows_inline_error(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    create, _ = _open_form_filled(
        super_admin_context, settings, overrides={"pinfl": f"7{_rd(13)}"}
    )
    create.submit()
    page = create.page
    expect(
        page.get_by_text("ПИНФЛ должен содержать 14 цифр и начинаться с 1–6")
    ).to_be_visible(timeout=settings.expect_timeout)
    _expect_form_stays(create, settings)


@pytest.mark.negative
@allure.title("UC-4.1 neg: пустые обязательные поля → submit не отправлен, форма остаётся")
def test_company_create_with_all_empty_fields_blocks_submit(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    create = CreateCompanyPage(page).goto(settings.admin_url)
    expect(create.page_heading).to_be_visible(timeout=settings.expect_timeout)
    create.submit()
    _expect_form_stays(create, settings)


@pytest.mark.negative
@allure.title("UC-4.1 neg: цифры в Имя → submit blocked фронт-валидацией, форма остаётся")
def test_company_create_with_digits_in_first_name_blocks_submit(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    """Helper-text "Только буквы, пробелы, дефис и апостроф" в форме —
    submit заблокирован фронтом, POST не уходит.
    """
    create, _ = _open_form_filled(
        super_admin_context, settings, overrides={"first_name": "Имя123"}
    )
    create.submit()
    _expect_form_stays(create, settings)
