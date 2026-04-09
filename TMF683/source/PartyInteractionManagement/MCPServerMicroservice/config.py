from __future__ import annotations

import os


class Config:
    BASE_URL: str = os.getenv("TMF683_BASE_URL", "http://localhost:8080")
    API_VERSION: str = os.getenv("TMF683_API_VERSION", "v5")
    API_TOKEN: str = os.getenv("TMF683_API_TOKEN", "")
    TIMEOUT_SECONDS: int = int(os.getenv("TMF683_TIMEOUT_SECONDS", "30"))
    MODE: str = os.getenv("TMF683_MODE", "mock").lower()
    HTTP_BASE_PATH: str = os.getenv("MCP_HTTP_BASE_PATH", "")
    SPEC_URL: str = os.getenv(
        "TMF683_SPEC_URL",
        "https://raw.githubusercontent.com/tmforum-apis/TMF683_PartyInteraction/main/TMF683-Party_Interaction-v5.0.0.oas.yaml",
    )
    SPEC_CACHE: str = os.getenv("TMF683_SPEC_CACHE", "./spec_cache/TMF683.json")
    VERIFY_SSL: bool = os.getenv("TMF683_VERIFY_SSL", "true").lower() not in {"false", "0", "no"}
    LOG_LEVEL: str = os.getenv("MCP_LOG_LEVEL", "INFO").upper()
    SERVER_NAME: str = "tmf683-party-interaction-management"
    SERVER_VERSION: str = "0.1.0"

    @property
    def api_base_path(self) -> str:
        return f"/tmf-api/partyInteractionManagement/{self.API_VERSION}"

    @property
    def http_base_path(self) -> str:
        base_path = self.HTTP_BASE_PATH.strip("/")
        return f"/{base_path}" if base_path else ""

    @property
    def mcp_path(self) -> str:
        return f"{self.http_base_path}/mcp" if self.http_base_path else "/mcp"

    @property
    def mcp_messages_path(self) -> str:
        return f"{self.mcp_path}/messages/"


config = Config()
