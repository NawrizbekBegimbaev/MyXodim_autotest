import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import Settings
from pages.client.sidebar import ADMIN_NAV, ClientSidebar


@pytest.mark.smoke
@allure.title("Client UI sidebar содержит все 17 ссылок и 4 подгруппы")
def test_sidebar_full_navigation_visible(
    client_admin_page: Page, settings: Settings
) -> None:
    client_admin_page.goto(f"{settings.client_url}/home", wait_until="networkidle")
    sidebar = ClientSidebar(client_admin_page)
    sidebar.expand_all_subgroups()
    for section, _subgroup, label, _path in ADMIN_NAV:
        with allure.step(f"Link «{label}» в section «{section}»"):
            expect(sidebar.link(label)).to_be_visible()
