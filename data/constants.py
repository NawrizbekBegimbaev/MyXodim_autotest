"""Общие константы. ВАЖНО: TEST_OTP работает только на dev (любой 6-значный)."""

TEST_OTP: str = "123456"

E2E_ORG_PREFIX: str = "[E2E]"
E2E_PREFIX: str = "[E2E]"

AUTH_DIR: str = ".auth"
SUPER_ADMIN_STATE_FILE: str = f"{AUTH_DIR}/super_admin.json"
CLIENT_ADMIN_STATE_FILE: str = f"{AUTH_DIR}/client_admin.json"
