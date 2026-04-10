from __future__ import annotations

import os


class Config:
    BASE_URL: str = os.getenv("TMF621_BASE_URL", os.getenv("TMF683_BASE_URL", "http://localhost:8080"))
    API_VERSION: str = os.getenv("TMF621_API_VERSION", os.getenv("TMF683_API_VERSION", "v5"))
    API_TOKEN: str = os.getenv("TMF621_API_TOKEN", os.getenv("TMF683_API_TOKEN", ""))
    TIMEOUT_SECONDS: int = int(os.getenv("TMF621_TIMEOUT_SECONDS", os.getenv("TMF683_TIMEOUT_SECONDS", "30")))
    MODE: str = os.getenv("TMF621_MODE", os.getenv("TMF683_MODE", "mock")).lower()
    HTTP_BASE_PATH: str = os.getenv("MCP_HTTP_BASE_PATH", "")
    SPEC_URL: str = os.getenv(
        "TMF621_SPEC_URL",
        os.getenv(
            "TMF683_SPEC_URL",
            "https://raw.githubusercontent.com/tmforum-apis/TMF621_TroubleTicket/main/TMF621-Trouble_Ticket-v5.0.1.oas.yaml",
        ),
    )
    SPEC_CACHE: str = os.getenv("TMF621_SPEC_CACHE", os.getenv("TMF683_SPEC_CACHE", "./spec_cache/TMF621.json"))
    VERIFY_SSL: bool = os.getenv("TMF621_VERIFY_SSL", os.getenv("TMF683_VERIFY_SSL", "true")).lower() not in {
        "false",
        "0",
        "no",
    }
    LOG_LEVEL: str = os.getenv("MCP_LOG_LEVEL", "INFO").upper()
    SERVER_NAME: str = "tmf621-trouble-ticket-management"
    SERVER_VERSION: str = "0.2.0"

    @property
    def api_base_path(self) -> str:
        return f"/tmf-api/troubleTicket/{self.API_VERSION}"

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
