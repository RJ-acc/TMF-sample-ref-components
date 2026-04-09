from __future__ import annotations

import logging
import os
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from common.api_directory import build_api_directory
from common.billing import (
    apply_customer_bill_patch,
    ensure_seed_data,
    generate_customer_bill_on_demand,
    list_applied_customer_billing_rates,
    list_bill_cycles,
)
from common.events import build_event, publish_event, utc_now
from common.store import get_store
from common.validation import validate_customer_bill_on_demand, validate_customer_bill_patch

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("tmfc030-bill-generation-api")

COMPONENT_NAME = os.getenv("COMPONENT_NAME", "billgenerationmanagement")
API_BASE_PATH = "/" + os.getenv("API_BASE_PATH", "/tmf-api/customerBillManagement/v5").strip("/")
ENGINE_SERVICE_URL = os.getenv("ENGINE_SERVICE_URL", "").rstrip("/")
API_VERSION = "5.0.0"
API_DIRECTORY_DESCRIPTION = """## TMF API Reference: TMF678 - Customer Bill Management

### Reference component: TMFC030 Bill Generation Management

Customer Bill Management API exposes read access to bill cycles, applied billing rates, customer bills,
and supports on-demand bill generation plus customer bill patch updates.

### Operations
- Retrieve bill cycles, applied customer billing rates, customer bills, and customer bill on-demand tasks
- Create customer bill on-demand tasks
- Partially update a customer bill
- Register and unregister event listeners
"""

LISTENER_OPERATIONS = [
    ("listenToCustomerBillCreateEvent", "/listener/customerBillCreateEvent"),
    ("listenToCustomerBillOnDemandCreateEvent", "/listener/customerBillOnDemandCreateEvent"),
    ("listenToCustomerBillOnDemandStateChangeEvent", "/listener/customerBillOnDemandStateChangeEvent"),
    ("listenToCustomerBillStateChangeEvent", "/listener/customerBillStateChangeEvent"),
]

app = FastAPI(
    title="TMFC030 Bill Generation Management API",
    docs_url=f"{API_BASE_PATH}/docs",
    openapi_url=f"{API_BASE_PATH}/openapi.json",
)
router = APIRouter(prefix=API_BASE_PATH)
store = get_store()


def _seed() -> None:
    ensure_seed_data(store)


def _href(resource_name: str, resource_id: str) -> str:
    return f"{API_BASE_PATH}/{resource_name}/{resource_id}"


def _select_fields(document: dict[str, Any], fields: str | None) -> dict[str, Any]:
    if not fields:
        return document
    selected = {}
    for field_name in [field.strip() for field in fields.split(",") if field.strip()]:
        if field_name in document:
            selected[field_name] = document[field_name]
    return selected


def _filters_from_request(request: Request) -> dict[str, Any]:
    return {
        key: value
        for key, value in request.query_params.items()
        if key not in {"fields", "offset", "limit"}
    }


def _response_status_code(payload: dict[str, Any]) -> int:
    return status.HTTP_200_OK if payload.get("instantSync") else status.HTTP_201_CREATED


async def _generate_on_demand(payload: dict[str, Any]) -> dict[str, Any]:
    if not ENGINE_SERVICE_URL:
        return generate_customer_bill_on_demand(payload)

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(f"{ENGINE_SERVICE_URL}/generate/customerBillOnDemand", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        logger.warning("Billing engine unavailable for on-demand flow, using in-process fallback: %s", exc)
        return generate_customer_bill_on_demand(payload)


async def _publish(event_type: str, resource_type: str, payload: dict[str, Any]) -> None:
    subscriptions = store.list_documents("subscriptions")
    await publish_event(subscriptions, build_event(event_type, resource_type, payload))


@app.get("/health")
async def health() -> dict[str, Any]:
    _seed()
    return {"status": "ok", "backend": store.backend, "component": COMPONENT_NAME}


@router.get("", include_in_schema=False)
@router.get("/", include_in_schema=False)
async def describe_customer_bill_api() -> dict[str, Any]:
    operations = [
        {
            "name": "listAppliedCustomerBillingRate",
            "href": "/appliedCustomerBillingRate",
            "method": "GET",
            "description": "List or find AppliedCustomerBillingRate objects",
        },
        {
            "name": "retrieveAppliedCustomerBillingRate",
            "href": "/appliedCustomerBillingRate/{id}",
            "method": "GET",
            "description": "Retrieves an AppliedCustomerBillingRate by ID",
        },
        {
            "name": "listBillCycle",
            "href": "/billCycle",
            "method": "GET",
            "description": "List or find BillCycle objects",
        },
        {
            "name": "retrieveBillCycle",
            "href": "/billCycle/{id}",
            "method": "GET",
            "description": "Retrieves a BillCycle by ID",
        },
        {
            "name": "listCustomerBill",
            "href": "/customerBill",
            "method": "GET",
            "description": "List or find CustomerBill objects",
        },
        {
            "name": "retrieveCustomerBill",
            "href": "/customerBill/{id}",
            "method": "GET",
            "description": "Retrieves a CustomerBill by ID",
        },
        {
            "name": "patchCustomerBill",
            "href": "/customerBill/{id}",
            "method": "PATCH",
            "description": "Updates partially a CustomerBill entity",
        },
        {
            "name": "listCustomerBillOnDemand",
            "href": "/customerBillOnDemand",
            "method": "GET",
            "description": "List or find CustomerBillOnDemand objects",
        },
        {
            "name": "createCustomerBillOnDemand",
            "href": "/customerBillOnDemand",
            "method": "POST",
            "description": "Creates a CustomerBillOnDemand task",
        },
        {
            "name": "retrieveCustomerBillOnDemand",
            "href": "/customerBillOnDemand/{id}",
            "method": "GET",
            "description": "Retrieves a CustomerBillOnDemand by ID",
        },
        {
            "name": "registerListener",
            "href": "/hub",
            "method": "POST",
            "description": "Create a subscription (hub) to receive Events",
        },
        {
            "name": "unregisterListener",
            "href": "/hub/{id}",
            "method": "DELETE",
            "description": "Remove a subscription (hub) to receive Events",
        },
    ]
    operations.extend(
        {
            "name": operation_name,
            "href": listener_path,
            "method": "POST",
            "description": f"Example client listener exposed at {listener_path}",
        }
        for operation_name, listener_path in LISTENER_OPERATIONS
    )

    return build_api_directory(
        base_path=API_BASE_PATH,
        title="Customer Bill Management",
        version=API_VERSION,
        description=API_DIRECTORY_DESCRIPTION,
        operations=operations,
    )


def _paged_documents(
    collection: str,
    request: Request,
    response: Response,
    fields: str | None,
    offset: int,
    limit: int,
) -> list[dict[str, Any]]:
    filters = _filters_from_request(request)
    all_documents = store.list_documents(collection, filters=filters)
    paged_documents = all_documents[max(offset, 0): max(offset, 0) + max(limit, 0)]
    response.headers["X-Total-Count"] = str(len(all_documents))
    response.headers["X-Result-Count"] = str(len(paged_documents))
    return [_select_fields(document, fields) for document in paged_documents]


@router.get("/appliedCustomerBillingRate")
async def list_applied_customer_billing_rate(
    request: Request,
    response: Response,
    fields: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    _seed()
    return _paged_documents("applied_customer_billing_rates", request, response, fields, offset, limit)


@router.get("/appliedCustomerBillingRate/{entity_id}")
async def retrieve_applied_customer_billing_rate(entity_id: str, fields: str | None = None) -> dict[str, Any]:
    _seed()
    document = store.get_document("applied_customer_billing_rates", entity_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"AppliedCustomerBillingRate '{entity_id}' not found")
    return _select_fields(document, fields)


@router.get("/billCycle")
async def list_bill_cycle(
    request: Request,
    response: Response,
    fields: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    _seed()
    return _paged_documents("bill_cycles", request, response, fields, offset, limit)


@router.get("/billCycle/{entity_id}")
async def retrieve_bill_cycle(entity_id: str, fields: str | None = None) -> dict[str, Any]:
    _seed()
    document = store.get_document("bill_cycles", entity_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"BillCycle '{entity_id}' not found")
    return _select_fields(document, fields)


@router.get("/customerBill")
async def list_customer_bill(
    request: Request,
    response: Response,
    fields: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    _seed()
    return _paged_documents("customer_bills", request, response, fields, offset, limit)


@router.get("/customerBill/{entity_id}")
async def retrieve_customer_bill(entity_id: str, fields: str | None = None) -> dict[str, Any]:
    _seed()
    document = store.get_document("customer_bills", entity_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"CustomerBill '{entity_id}' not found")
    return _select_fields(document, fields)


@router.patch("/customerBill/{entity_id}")
async def patch_customer_bill(entity_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    _seed()
    existing = store.get_document("customer_bills", entity_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"CustomerBill '{entity_id}' not found")

    validation = validate_customer_bill_patch(patch)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation)

    previous_state = existing.get("state")
    updated = apply_customer_bill_patch(existing, patch)
    store.replace_document("customer_bills", entity_id, updated)

    if updated.get("state") != previous_state:
        await _publish("CustomerBillStateChangeEvent", "customerBill", updated)

    return updated


@router.get("/customerBillOnDemand")
async def list_customer_bill_on_demand(
    request: Request,
    response: Response,
    fields: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    _seed()
    return _paged_documents("customer_bill_on_demand", request, response, fields, offset, limit)


@router.post("/customerBillOnDemand", status_code=status.HTTP_201_CREATED)
async def create_customer_bill_on_demand(payload: dict[str, Any]) -> JSONResponse:
    _seed()
    generation = await _generate_on_demand(payload)
    validation = generation.get("validation") or validate_customer_bill_on_demand(payload)
    entity_id = payload.get("id") or str(uuid4())[:8]

    entity = {
        **(generation.get("customerBillOnDemand") or payload),
        "id": entity_id,
        "href": _href("customerBillOnDemand", entity_id),
        "state": payload.get("state") or ("done" if validation["valid"] else "terminatedWithError"),
        "lastUpdate": utc_now(),
        "validationResult": validation,
        "processingSummary": generation.get("summary", {}),
        "@type": payload.get("@type", "CustomerBillOnDemand"),
    }

    generated_bill = generation.get("customerBill")
    if generated_bill:
        bill_id = generated_bill.get("id") or f"cb-{entity_id}"
        generated_bill = {
            **generated_bill,
            "id": bill_id,
            "href": _href("customerBill", bill_id),
            "lastUpdate": utc_now(),
            "@type": generated_bill.get("@type", "CustomerBill"),
        }
        entity["customerBill"] = {
            "id": bill_id,
            "href": generated_bill["href"],
            "name": generated_bill.get("name"),
            "@referredType": "CustomerBill",
            "@type": "CustomerBillRef",
        }

    try:
        store.create_document("customer_bill_on_demand", entity)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if generated_bill:
        try:
            store.create_document("customer_bills", generated_bill)
        except ValueError:
            store.replace_document("customer_bills", generated_bill["id"], generated_bill)
        await _publish("CustomerBillCreateEvent", "customerBill", generated_bill)

    await _publish("CustomerBillOnDemandCreateEvent", "customerBillOnDemand", entity)
    await _publish("CustomerBillOnDemandStateChangeEvent", "customerBillOnDemand", entity)
    return JSONResponse(content=entity, status_code=_response_status_code(payload))


@router.get("/customerBillOnDemand/{entity_id}")
async def retrieve_customer_bill_on_demand(entity_id: str, fields: str | None = None) -> dict[str, Any]:
    _seed()
    document = store.get_document("customer_bill_on_demand", entity_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"CustomerBillOnDemand '{entity_id}' not found")
    return _select_fields(document, fields)


@router.post("/hub", status_code=status.HTTP_201_CREATED)
async def register_listener(payload: dict[str, Any]) -> dict[str, Any]:
    callback = payload.get("callback")
    if not callback:
        raise HTTPException(status_code=400, detail="callback is required")

    query = payload.get("query", "")
    for existing in store.list_documents("subscriptions"):
        if existing.get("callback") == callback and existing.get("query", "") == query:
            return existing

    subscription_id = payload.get("id") or str(uuid4())[:8]
    entity = {
        "id": subscription_id,
        "href": _href("hub", subscription_id),
        "callback": callback,
        "query": query,
        "lastUpdate": utc_now(),
        "@type": payload.get("@type", "EventSubscription"),
    }
    store.create_document("subscriptions", entity)
    return entity


@router.delete("/hub/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_listener(subscription_id: str) -> Response:
    deleted = store.delete_document("subscriptions", subscription_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Subscription '{subscription_id}' not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _receive_listener_event(payload: dict[str, Any]) -> Response:
    logger.info("Received listener example payload with keys: %s", sorted(payload.keys()))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


for listener_name, listener_path in LISTENER_OPERATIONS:
    router.add_api_route(
        listener_path,
        _receive_listener_event,
        methods=["POST"],
        name=listener_name,
        status_code=status.HTTP_204_NO_CONTENT,
    )


app.include_router(router)
