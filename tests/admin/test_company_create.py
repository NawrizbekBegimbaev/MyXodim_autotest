"""UC-4.1: создание компании Super Admin'ом в Admin UI.

BRD §4.1: создание организации с первым Администратором.
В UI домен называется "Компания" (URL /tenants), форма /tenants/new.
"""

from __future__ import annotations

import secrets
import uuid

import allure
import pytest
from playwright.sync_api import BrowserContext, expect

from config.settings import Settings
from data.constants import E2E_ORG_PREFIX
from data.i18n import t
from pages.admin.create_company_page import CompanyCreatedView, CreateCompanyPage
from pages.admin.organizations_page import OrganizationsPage


def _rand_digits(n: int) -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(n))


def _valid_pinfl() -> str:
    """UZ ПИНФЛ: 14 цифр, первая 1-6 (фронт-валидация enforced)."""
    return f"{secrets.randbelow(6) + 1}{_rand_digits(13)}"


def _generate_test_data() -> dict[str, str]:
    suffix = uuid.uuid4().hex[:6]
    return {
        "name": f"{E2E_ORG_PREFIX} {suffix}",
        "slug": f"e2e-{suffix}",
        "inn": _rand_digits(9),
        "first_name": "Тест",
        "last_name": "Администратор",
        "phone_local": f"905{_rand_digits(7)}",
        "pinfl": _valid_pinfl(),
        "suffix": suffix,
    }


@pytest.mark.positive
@allure.title("UC-4.1: создание компании с валидными данными → success-page с ключом")
def test_company_create_with_valid_data_returns_integration_key(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    data = _generate_test_data()

    create = CreateCompanyPage(page).goto(settings.admin_url)
    with allure.step("Форма создания компании открыта"):
        expect(create.page_heading).to_be_visible(timeout=settings.expect_timeout)

    with allure.step(f"Заполняем компанию (name={data['name']}, slug={data['slug']})"):
        create.fill_company(name=data["name"], slug=data["slug"], inn=data["inn"])

    with allure.step("Заполняем администратора с ПИНФЛ"):
        create.fill_admin(
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone_local=data["phone_local"],
            pinfl=data["pinfl"],
        )

    with allure.step("Submit"):
        create.submit()

    success = CompanyCreatedView(page)
    with allure.step("Success-state с ключом интеграции и UUID-ами"):
        # Submit инициирует POST на бэк + переход в success-state. Иногда дольше 10s.
        expect(success.heading).to_be_visible(timeout=settings.nav_timeout)
        expect(success.integration_key_locator).to_be_visible()

        integration_key = success.integration_key()
        tenant_id = success.tenant_id()
        admin_user_id = success.admin_user_id()

        allure.attach(
            f"key={integration_key}\ntenant_id={tenant_id}\nadmin_id={admin_user_id}",
            name="created-company",
            attachment_type=allure.attachment_type.TEXT,
        )

        assert CompanyCreatedView.INTEGRATION_KEY_PATTERN.match(integration_key), (
            f"integration_key '{integration_key}' не соответствует bh_live_<32hex>"
        )
        assert CompanyCreatedView.UUID_PATTERN.match(tenant_id), f"tenant_id '{tenant_id}' не UUID"
        assert CompanyCreatedView.UUID_PATTERN.match(admin_user_id), (
            f"admin_user_id '{admin_user_id}' не UUID"
        )


@pytest.mark.positive
@allure.title("UC-4.2: созданная компания видна в списке /tenants со статусом Активна")
def test_company_appears_in_tenants_list_after_creation(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    page = super_admin_context.new_page()
    data = _generate_test_data()

    CreateCompanyPage(page).goto(settings.admin_url).fill_company(
        name=data["name"], slug=data["slug"], inn=data["inn"]
    ).fill_admin(
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone_local=data["phone_local"],
        pinfl=data["pinfl"],
    ).submit()

    success = CompanyCreatedView(page)
    expect(success.heading).to_be_visible(timeout=settings.nav_timeout)

    with allure.step("Список компаний с retry (eventual consistency бэка)"):
        # POST 200, но GET /tenants может вернуть старый список —
        # write-to-read задержка на бэке. Делаем reload-loop до 30s.
        list_page = super_admin_context.new_page()
        orgs = OrganizationsPage(list_page)
        deadline_ms = 30_000
        elapsed_ms = 0
        step_ms = 2_000
        while elapsed_ms < deadline_ms:
            list_page.goto(f"{settings.admin_url}/tenants", wait_until="networkidle")
            expect(orgs.heading).to_be_visible(timeout=settings.nav_timeout)
            row = orgs.row_by_name(data["suffix"])
            if row.count() > 0 and row.first.is_visible():
                break
            list_page.wait_for_timeout(step_ms)
            elapsed_ms += step_ms

    with allure.step("Компания видна со статусом Активна"):
        row = orgs.row_by_name(data["suffix"])
        expect(row).to_be_visible(timeout=settings.expect_timeout)
        expect(row).to_contain_text(t("org.status_active"))


@pytest.mark.negative
@allure.title("UC-4.1 negative: без ИНН → 400, форма остаётся открытой")
def test_company_create_without_inn_stays_on_form(
    super_admin_context: BrowserContext, settings: Settings
) -> None:
    """ИНН без звёздочки на форме, но обязателен на бэке (BUG-002 extended).

    Бэк отвечает 400 constraint-violations. Тест проверяет что НЕ происходит
    редирект на success-state, форма остаётся открытой.
    """
    page = super_admin_context.new_page()
    data = _generate_test_data()

    create = CreateCompanyPage(page).goto(settings.admin_url)
    create.fill_company(name=data["name"], slug=data["slug"])  # без ИНН
    create.fill_admin(
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone_local=data["phone_local"],
        pinfl=data["pinfl"],
    )
    create.submit()

    with allure.step("Форма не уходит в success — heading 'Новая компания' виден"):
        # Дать бэку и фронту обработать 400
        page.wait_for_load_state("networkidle", timeout=settings.nav_timeout)
        expect(create.page_heading).to_be_visible(timeout=settings.expect_timeout)
        # success-heading НЕ должен появиться
        success_heading = page.get_by_role("heading", name="Компания создана", level=5)
        expect(success_heading).not_to_be_visible()
