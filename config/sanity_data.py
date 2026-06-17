"""Unique test-data generation for daily sanity runs.

Policy (agreed): create with a unique [SANITY] name and leave it — no cleanup.
Names/phones/INN/PINFL are made unique per run from the epoch so daily runs
never collide.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


def _suffix() -> str:
    # 7 trailing digits of epoch seconds — unique enough for daily cadence.
    return str(int(time.time()))[-7:]


@dataclass(frozen=True)
class SanityTenantData:
    suffix: str = field(default_factory=_suffix)

    @property
    def name(self) -> str:
        return f"[SANITY] {self.suffix}"

    @property
    def slug(self) -> str:
        return f"sanity-{self.suffix}"

    @property
    def inn(self) -> str:
        # 9-digit, unique per run.
        return f"9{self.suffix}0"[:9].ljust(9, "0")

    @property
    def admin_first_name(self) -> str:
        return "Санити"

    @property
    def admin_last_name(self) -> str:
        return "Тестов"

    @property
    def admin_phone(self) -> str:
        # +998 90 XXXXXXX (7 digits) -> registered, OTP login works on staging.
        return f"+99890{self.suffix}"

    @property
    def admin_pinfl(self) -> str:
        # 14-digit, starts with valid century digit.
        return f"3{self.suffix}000000"[:14].ljust(14, "0")


@dataclass(frozen=True)
class SanityAdminData:
    """Platform admin created in Admin UI (case 3)."""

    suffix: str = field(default_factory=_suffix)

    @property
    def first_name(self) -> str:
        return "Санити"

    @property
    def last_name(self) -> str:
        return f"Админ{self.suffix}"

    @property
    def phone(self) -> str:
        return f"+99891{self.suffix}"
