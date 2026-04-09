from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from common.billing import (
    STARTER_CUSTOMER_BILLS,
    generate_customer_bill_on_demand,
    list_applied_customer_billing_rates,
    list_bill_cycles,
)
from common.validation import validate_customer_bill_on_demand, validate_customer_bill_patch

app = FastAPI(title="TMFC030 Bill Generation Engine Service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/billCycle")
async def bill_cycle() -> dict[str, Any]:
    cycles = list_bill_cycles()
    return {"count": len(cycles), "items": cycles}


@app.get("/appliedCustomerBillingRate")
async def applied_customer_billing_rate() -> dict[str, Any]:
    rates = list_applied_customer_billing_rates()
    return {"count": len(rates), "items": rates}


@app.get("/customerBill")
async def customer_bill() -> dict[str, Any]:
    return {"count": len(STARTER_CUSTOMER_BILLS), "items": STARTER_CUSTOMER_BILLS}


@app.post("/validate/customerBillOnDemand")
async def validate_customer_bill_on_demand_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return validate_customer_bill_on_demand(payload)


@app.post("/validate/customerBillPatch")
async def validate_customer_bill_patch_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return validate_customer_bill_patch(payload)


@app.post("/generate/customerBillOnDemand")
async def generate_customer_bill_on_demand_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return generate_customer_bill_on_demand(payload)
