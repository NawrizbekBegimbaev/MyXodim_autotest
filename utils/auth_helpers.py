"""Хелперы для UI-логина. БЕЗ HTTP-вызовов."""

from playwright.sync_api import BrowserContext, Page

from data.constants import TEST_OTP
from pages.client.login_page import ClientLoginPage
from pages.client.otp_page import OtpPage
from pages.client.select_organization_page import SelectOrganizationPage


def login_client_via_otp(
    context: BrowserContext,
    base_url: str,
    phone: str,
    organization: str | None = None,
) -> Page:
    """UI-логин в Client UI через OTP (dev принимает любой 6-значный).

    Если пользователь состоит в нескольких организациях — попадает на /tenant-select.
    Передай `organization` чтобы выбрать нужную; иначе экран будет проигнорирован
    (актуально когда пользователь в одной орг — фронт пропускает выбор).
    """
    page = context.new_page()
    ClientLoginPage(page).goto(base_url).enter_phone(phone).submit()
    OtpPage(page).enter_code(TEST_OTP).submit()
    if organization is not None:
        SelectOrganizationPage(page).select(organization)
    return page
