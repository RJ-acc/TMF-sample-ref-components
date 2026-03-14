from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from common.validation import (
    ORDER_ACTIONS,
    ORDER_ITEM_STATES,
    ORDER_STATES,
    TASK_STATES,
    validate_cancel_product_order,
    validate_product_order,
)

app = FastAPI(title="TMFC002 Order Validation Service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/rules")
async def rules() -> dict[str, Any]:
    return {
        "orderStates": sorted(ORDER_STATES),
        "orderItemStates": sorted(ORDER_ITEM_STATES),
        "orderActions": sorted(ORDER_ACTIONS),
        "taskStates": sorted(TASK_STATES),
    }


@app.post("/validate/productOrder")
async def validate_product_order_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return validate_product_order(payload)


@app.post("/validate/cancelProductOrder")
async def validate_cancel_product_order_payload(
    payload: dict[str, Any],
    productOrderExists: bool | None = None,
) -> dict[str, Any]:
    return validate_cancel_product_order(payload, product_order_exists=productOrderExists)
