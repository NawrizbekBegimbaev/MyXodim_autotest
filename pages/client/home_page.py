import re
from typing import Self

from playwright.sync_api import Locator, Page

from data.i18n import t
from pages.base_page import BasePage


class HomePage(BasePage):
    """Client UI workspace landing at /home."""

    URL_PATH = "/home"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._greeting: Locator = page.get_by_role("heading", level=1)
        self._widget_payslip: Locator = page.get_by_role(
            "button", name=re.compile(rf"^{re.escape(t('client.home.widget_payslip'))}")
        ).first
        self._widget_payslip_heading: Locator = page.get_by_role(
            "heading", name=t("client.home.widget_payslip"), level=6
        )
        self._widget_vacation: Locator = page.get_by_role(
            "heading", name=t("client.home.widget_vacation"), level=6
        )
        self._widget_schedule: Locator = page.get_by_role(
            "heading", name=t("client.home.widget_schedule"), level=6
        )
        self._widget_my_docs: Locator = page.get_by_role(
            "heading", name=t("client.home.widget_my_docs"), level=6
        )
        self._widget_my_tasks: Locator = page.get_by_role(
            "heading", name=t("client.home.widget_my_tasks"), level=6
        )
        self._goto_payslip: Locator = page.get_by_role(
            "button", name=re.compile(rf"^{re.escape(t('client.home.widget_payslip'))}")
        ).first
        self._goto_vacation: Locator = page.get_by_role(
            "button", name=re.compile(rf"^{re.escape(t('client.home.widget_vacation'))}")
        ).first
        self._goto_schedule: Locator = page.get_by_role(
            "button", name=re.compile(rf"^{re.escape(t('client.home.widget_schedule'))}")
        ).first
        self._goto_vacation_cta: Locator = page.get_by_role(
            "button", name="Подробнее →"
        ).nth(0)
        self._goto_schedule_cta: Locator = page.get_by_role(
            "button", name="Подробнее →"
        ).nth(1)
        self._my_docs_in_work: Locator = page.get_by_text("В работе", exact=True)
        self._my_docs_pending: Locator = page.get_by_text("В ожидании", exact=True)
        self._my_docs_completed: Locator = page.get_by_text("Завершено", exact=True)
        self._my_docs_rejected: Locator = page.get_by_text("Отказано", exact=True)
        self._my_tasks_pending: Locator = page.get_by_text(
            "Ожидает согласования", exact=True
        )
        self._my_tasks_approved: Locator = page.get_by_text("Утверждено", exact=True)
        self._my_tasks_rejected: Locator = page.get_by_text(
            "Отказано", exact=True
        ).nth(1)

    @property
    def greeting(self) -> Locator:
        return self._greeting

    @property
    def widget_payslip(self) -> Locator:
        return self._widget_payslip

    @property
    def widget_payslip_heading(self) -> Locator:
        return self._widget_payslip_heading

    @property
    def widget_vacation(self) -> Locator:
        return self._widget_vacation

    @property
    def widget_schedule(self) -> Locator:
        return self._widget_schedule

    @property
    def widget_my_docs(self) -> Locator:
        return self._widget_my_docs

    @property
    def widget_my_tasks(self) -> Locator:
        return self._widget_my_tasks

    @property
    def my_docs_in_work(self) -> Locator:
        return self._my_docs_in_work

    @property
    def my_docs_pending(self) -> Locator:
        return self._my_docs_pending

    @property
    def my_docs_completed(self) -> Locator:
        return self._my_docs_completed

    @property
    def my_docs_rejected(self) -> Locator:
        return self._my_docs_rejected

    @property
    def my_tasks_pending(self) -> Locator:
        return self._my_tasks_pending

    @property
    def my_tasks_approved(self) -> Locator:
        return self._my_tasks_approved

    @property
    def my_tasks_rejected(self) -> Locator:
        return self._my_tasks_rejected

    def goto_payslip(self) -> Self:
        self._goto_payslip.click()
        return self

    def goto_vacation(self) -> Self:
        if self._goto_vacation.count() > 0:
            self._goto_vacation.click()
        else:
            self._goto_vacation_cta.click()
        return self

    def goto_schedule(self) -> Self:
        if self._goto_schedule.count() > 0:
            self._goto_schedule.click()
        else:
            self._goto_schedule_cta.click()
        return self
