from __future__ import annotations

import os


class Config:
    BASE_URL: str = os.getenv("TMF680_BASE_URL", "http://localhost:8080")
    API_VERSION: str = os.getenv("TMF680_API_VERSION", "v4")
    API_TOKEN: str = os.getenv("TMF680_API_TOKEN", "")
    TIMEOUT_SECONDS: int = int(os.getenv("TMF680_TIMEOUT_SECONDS", "30"))
    MODE: str = os.getenv("TMF680_MODE", "mock").lower()
    HTTP_BASE_PATH: str = os.getenv("MCP_HTTP_BASE_PATH", "")
    SPEC_URL: str = os.getenv(
        "TMF680_SPEC_URL",
        "https://raw.githubusercontent.com/tmforum-apis/TMF680_Recommendation/main/TMF680_Recommendation_Management_API_v4.0.0_swagger.json",
    )
    SPEC_CACHE: str = os.getenv("TMF680_SPEC_CACHE", "./spec_cache/TMF680.json")
    VERIFY_SSL: bool = os.getenv("TMF680_VERIFY_SSL", "true").lower() not in {"false", "0", "no"}
    LOG_LEVEL: str = os.getenv("MCP_LOG_LEVEL", "INFO").upper()
    SERVER_NAME: str = "tmf680-product-recommendation"
    SERVER_VERSION: str = "0.1.0"

    @property
    def api_base_path(self) -> str:
        return f"/tmf-api/recommendationManagement/{self.API_VERSION}"

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
