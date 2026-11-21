import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv(override=True)


@dataclass
class Settings:
    # Gemini LLM
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest").strip()

    # Data mode: "true", "false", or "auto"
    use_mock_data: str = os.getenv("USE_MOCK_DATA", "auto").strip().lower()

    # Azure DevOps
    ado_org_url: str = os.getenv("ADO_ORG_URL", "https://dev.azure.com/proglint").strip().rstrip("/")
    ado_project: str = os.getenv("ADO_PROJECT", "").strip()
    ado_pat: str = os.getenv("ADO_PAT", "").strip()

    # Microsoft Graph (Outlook Calendar) - supports AZURE_* or ENTRA_*
    azure_tenant_id: str = (os.getenv("AZURE_TENANT_ID") or os.getenv("ENTRA_TENANT_ID") or "").strip()
    azure_client_id: str = (os.getenv("AZURE_CLIENT_ID") or os.getenv("ENTRA_CLIENT_ID") or "").strip()
    azure_client_secret: str = (os.getenv("AZURE_CLIENT_SECRET") or os.getenv("ENTRA_CLIENT_SECRET") or "").strip()

    @property
    def is_gemini_configured(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def is_ado_configured(self) -> bool:
        return bool(self.ado_org_url and self.ado_pat)

    @property
    def is_outlook_configured(self) -> bool:
        # Configured if Tenant ID and Client ID are present (can use Secret OR Device/Interactive login)
        return bool(self.azure_tenant_id and self.azure_client_id)

    def should_mock(self, connector_configured: bool) -> bool:
        if self.use_mock_data == "true":
            return True
        if self.use_mock_data == "false":
            return False
        # "auto" mode: use live API if configured, otherwise fallback to mock
        return not connector_configured


def get_settings() -> Settings:
    load_dotenv(override=True)
    return Settings()
