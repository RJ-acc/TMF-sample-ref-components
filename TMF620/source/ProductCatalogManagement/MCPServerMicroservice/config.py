from __future__ import annotations

import os


class Config:
    BASE_URL: str = os.getenv("TMF620_BASE_URL", "http://localhost:8080")
    API_VERSION: str = os.getenv("TMF620_API_VERSION", "v5")
    API_TOKEN: str = os.getenv("TMF620_API_TOKEN", "")
    TIMEOUT_SECONDS: int = int(os.getenv("TMF620_TIMEOUT_SECONDS", "30"))
    MODE: str = os.getenv("TMF620_MODE", "mock").lower()
    HTTP_BASE_PATH: str = os.getenv("MCP_HTTP_BASE_PATH", "")
    SPEC_URL: str = os.getenv(
        "TMF620_SPEC_URL",
        "https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/main/TMF620-Product_Catalog_Management-v5.0.0.oas.yaml",
    )
    SPEC_CACHE: str = os.getenv("TMF620_SPEC_CACHE", "./spec_cache/TMF620.json")
    VERIFY_SSL: bool = os.getenv("TMF620_VERIFY_SSL", "true").lower() not in {"false", "0", "no"}
    LOG_LEVEL: str = os.getenv("MCP_LOG_LEVEL", "INFO").upper()
    SERVER_NAME: str = "tmf620-product-catalog-management"
    SERVER_VERSION: str = "0.1.0"

    @property
    def api_base_path(self) -> str:
        return f"/tmf-api/productCatalogManagement/{self.API_VERSION}"

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
