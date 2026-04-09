from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from common.configurations import STARTER_CATALOG, evaluate_check_product_configuration, generate_query_product_configuration
from common.validation import STARTER_CHANNELS, TASK_STATES, validate_check_product_configuration, validate_query_product_configuration

app = FastAPI(title="TMFC027 Product Configuration Engine Service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/rules")
async def rules() -> dict[str, Any]:
    return {
        "taskStates": sorted(TASK_STATES),
        "channels": sorted(STARTER_CHANNELS),
        "starterOfferings": [entry["id"] for entry in STARTER_CATALOG],
    }


@app.get("/catalog")
async def catalog() -> dict[str, Any]:
    return {"count": len(STARTER_CATALOG), "items": STARTER_CATALOG}


@app.post("/validate/queryProductConfiguration")
async def validate_query_product_configuration_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return validate_query_product_configuration(payload)


@app.post("/validate/checkProductConfiguration")
async def validate_check_product_configuration_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return validate_check_product_configuration(payload)


@app.post("/configure/queryProductConfiguration")
async def configure_query_product_configuration(payload: dict[str, Any]) -> dict[str, Any]:
    return generate_query_product_configuration(payload)


@app.post("/check/checkProductConfiguration")
async def check_product_configuration(payload: dict[str, Any]) -> dict[str, Any]:
    return evaluate_check_product_configuration(payload)
