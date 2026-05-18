"""Общие константы. ВАЖНО: TEST_OTP работает только на dev (любой 6-значный)."""

TEST_OTP: str = "123456"

E2E_ORG_PREFIX: str = "[E2E]"
E2E_PREFIX: str = "[E2E]"

AUTH_DIR: str = ".auth"
SUPER_ADMIN_STATE_FILE: str = f"{AUTH_DIR}/super_admin.json"
CLIENT_ADMIN_STATE_FILE: str = f"{AUTH_DIR}/client_admin.json"

RECON_TENANT_NAME: str = "[E2E recon] 8dgk1l"
RECON_TENANT_SLUG: str = "e2e-recon-8dgk1l"
RECON_TENANT_ID: str = "a51f7085-95a4-4b71-930f-30ef974c418e"
RECON_ADMIN_PHONE: str = "+998905555518"
