from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    BASE_URL: str = os.getenv("TMF622_BASE_URL", "http://localhost:8080")
    API_VERSION: str = os.getenv("TMF622_API_VERSION", "v4")
    API_TOKEN: str = os.getenv("TMF622_API_TOKEN", "")
    TIMEOUT_SECONDS: int = int(os.getenv("TMF622_TIMEOUT_SECONDS", "30"))
    MODE: str = os.getenv("TMF622_MODE", "mock").lower()
    SPEC_URL: str = os.getenv(
        "TMF622_SPEC_URL",
        "https://raw.githubusercontent.com/tmforum-apis/TMF622_ProductOrder/main/TMF622-ProductOrder-v4.0.0.swagger.json",
    )
    SPEC_CACHE: str = os.getenv("TMF622_SPEC_CACHE", "./spec_cache/TMF622.json")
    VERIFY_SSL: bool = os.getenv("TMF622_VERIFY_SSL", "true").lower() not in {"false", "0", "no"}
    LOG_LEVEL: str = os.getenv("MCP_LOG_LEVEL", "INFO").upper()
    SERVER_NAME: str = "tmf622-product-order"
    SERVER_VERSION: str = "0.1.0"

    @property
    def api_base_path(self) -> str:
        return f"/tmf-api/productOrderingManagement/{self.API_VERSION}"


config = Config()

