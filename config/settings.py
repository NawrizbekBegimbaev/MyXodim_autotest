from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    admin_url: str = Field(default="https://dev-hub-admin.greatmall.uz")
    client_url: str = Field(default="https://dev-hub-client.greatmall.uz")
    mock1c_url: str = Field(default="https://dev-mock-1c.greatmall.uz")

    super_admin_phone: str = Field(default="+998991234567")
    super_admin_password: str = Field(default="")

    # Существующий тестовый сотрудник в Client UI на dev — для smoke логина.
    # В обычных тестах сотрудники создаются на лету (см. CLAUDE.md §5).
    client_smoke_phone: str = Field(default="+998905555518")
    # Тестовая орг для positive Client UI тестов (пока BUG-001 блокирует
    # создание новых компаний). Должна существовать на dev и client_smoke_phone
    # должен быть Администратором в ней.
    client_smoke_org: str = Field(default="[E2E recon] 8dgk1l")

    mock1c_username: str = Field(default="")
    mock1c_password: str = Field(default="")

    test_otp: str = Field(default="123456")
    phone_pool_start: int = Field(default=1)
    phone_pool_size: int = Field(default=50)

    expect_timeout: int = Field(default=10_000)
    nav_timeout: int = Field(default=15_000)

    eimzo_pin_remembered: bool = Field(default=True)
