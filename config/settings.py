"""Central config for the MyXodim sanity suite, loaded from .env."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Base URLs (staging defaults)
    client_url: str = "https://myxodim-stage.greatmall.uz"
    admin_url: str = "https://myxodim-admin-stage.greatmall.uz"
    mock1c_url: str = "https://mock1c-stage.greatmall.uz"
    api_url: str = "https://myxodim-api-stage.greatmall.uz"

    # Client login (staging accepts any 6-digit OTP for a registered phone)
    client_phone: str = "+998994002396"
    test_otp: str = "123456"

    # A known EMPLOYEE-role user (restricted access) for the RBAC case.
    client_employee_phone: str = "+998994002396"

    # Admin login
    admin_phone: str = "+998991234567"
    admin_password: str = "admin123"

    # Locale used for RU/UZ text assertions
    locale: str = "ru"

    # Happy-path template
    sanity_template_name: str = "Заявление на отпуск"


settings = Settings()
