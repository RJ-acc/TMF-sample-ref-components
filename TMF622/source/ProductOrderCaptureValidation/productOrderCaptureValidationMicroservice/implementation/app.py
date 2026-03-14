from __future__ import annotations

import copy
import logging
import os
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, FastAPI, HTTPException, Request, Response, status

from common.api_directory import build_api_directory
from common.events import build_event, publish_event, utc_now
from common.store import get_store
from common.validation import validate_cancel_product_order, validate_product_order

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("tmfc002-product-order-api")

COMPONENT_NAME = os.getenv("COMPONENT_NAME", "productordercapturevalidation")
API_BASE_PATH = "/" + os.getenv("API_BASE_PATH", "/tmf-api/productOrderingManagement/v4").strip("/")
VALIDATION_SERVICE_URL = os.getenv("VALIDATION_SERVICE_URL", "http://localhost:8081").rstrip("/")
API_VERSION = "4.0.0"
API_DIRECTORY_DESCRIPTION = """## TMF API Reference: TMF622 - Product Ordering Management

### Reference component: TMFC002 Product Order Capture & Validation

Product Ordering Management API supports product order capture, validation-aware state handling,
cancel product order workflows, and event subscription management.

### Operations
- Retrieve an entity or a collection of entities depending on filter criteria
- Create a product order or cancel product order task
- Partially update an entity
- Delete a product order
- Register and unregister event listeners
"""

app = FastAPI(
    title="TMFC002 Product Order Capture & Validation API",
    docs_url=f"{API_BASE_PATH}/docs",
    openapi_url=f"{API_BASE_PATH}/openapi.json",
)
router = APIRouter(prefix=API_BASE_PATH)
store = get_store()


def _select_fields(document: dict[str, Any], fields: str | None) -> dict[str, Any]:
    if not fields:
        return document
    selected = {}
    for field_name in [field.strip() for field in fields.split(",") if field.strip()]:
        if field_name in document:
            selected[field_name] = document[field_name]
    return selected


def _href(resource_name: str, resource_id: str) -> str:
    return f"{API_BASE_PATH}/{resource_name}/{resource_id}"


def _merge_document(existing: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(existing)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_document(merged[key], value)
        else:
            merged[key] = value
    return merged


def _filters_from_request(request: Request) -> dict[str, Any]:
    return {
        key: value
        for key, value in request.query_params.items()
        if key not in {"fields", "offset", "limit"}
    }


def _prepare_order_items(items: list[dict[str, Any]], valid: bool) -> list[dict[str, Any]]:
    prepared = []
    default_state = "acknowledged" if valid else "held"
    for index, item in enumerate(items or [], start=1):
        candidate = copy.deepcopy(item)
        candidate.setdefault("id", str(index))
        candidate.setdefault("state", default_state)
        prepared.append(candidate)
    return prepared


async def _validate_order(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(f"{VALIDATION_SERVICE_URL}/validate/productOrder", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        logger.warning("Validation service unavailable, falling back to in-process validation: %s", exc)
        return validate_product_order(payload)


async def _validate_cancel_order(payload: dict[str, Any], product_order_exists: bool) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(
                f"{VALIDATION_SERVICE_URL}/validate/cancelProductOrder",
                params={"productOrderExists": str(product_order_exists).lower()},
                json=payload,
            )
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        logger.warning("Cancel validation service unavailable, falling back to in-process validation: %s", exc)
        return validate_cancel_product_order(payload, product_order_exists=product_order_exists)


async def _publish(event_type: str, resource_type: str, payload: dict[str, Any]) -> None:
    subscriptions = store.list_documents("subscriptions")
    await publish_event(subscriptions, build_event(event_type, resource_type, payload))


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "backend": store.backend, "component": COMPONENT_NAME}


@router.get("", include_in_schema=False)
@router.get("/", include_in_schema=False)
async def describe_product_order_api() -> dict[str, Any]:
    return build_api_directory(
        base_path=API_BASE_PATH,
        title="Product Ordering Management",
        version=API_VERSION,
        description=API_DIRECTORY_DESCRIPTION,
        operations=[
            {
                "name": "listProductOrder",
                "href": "/productOrder",
                "method": "GET",
                "description": "This operation list or find ProductOrder entities",
            },
            {
                "name": "createProductOrder",
                "href": "/productOrder",
                "method": "POST",
                "description": "This operation creates a ProductOrder entity.",
            },
            {
                "name": "retrieveProductOrder",
                "href": "/productOrder/{id}",
                "method": "GET",
                "description": "This operation retrieves a ProductOrder entity. Attribute selection is enabled for all first level attributes.",
            },
            {
                "name": "patchProductOrder",
                "href": "/productOrder/{id}",
                "method": "PATCH",
                "description": "This operation updates partially a ProductOrder entity.",
            },
            {
                "name": "deleteProductOrder",
                "href": "/productOrder/{id}",
                "method": "DELETE",
                "description": "This operation deletes a ProductOrder entity.",
            },
            {
                "name": "listCancelProductOrder",
                "href": "/cancelProductOrder",
                "method": "GET",
                "description": "This operation list or find CancelProductOrder entities",
            },
            {
                "name": "createCancelProductOrder",
                "href": "/cancelProductOrder",
                "method": "POST",
                "description": "This operation creates a CancelProductOrder entity.",
            },
            {
                "name": "retrieveCancelProductOrder",
                "href": "/cancelProductOrder/{id}",
                "method": "GET",
                "description": "This operation retrieves a CancelProductOrder entity. Attribute selection is enabled for all first level attributes.",
            },
            {
                "name": "registerListener",
                "href": "/hub",
                "method": "POST",
                "description": "Sets the communication endpoint address the service instance must use to deliver notifications.",
            },
            {
                "name": "unregisterListener",
                "href": "/hub/{id}",
                "method": "DELETE",
                "description": "Resets the communication endpoint address the service instance must use to deliver notifications.",
            },
            {
                "name": "listenToProductOrderCreateEvent",
                "href": "/listener/productOrderCreateEvent",
                "method": "POST",
                "description": "Example of a client listener for receiving the notification ProductOrderCreateEvent",
            },
            {
                "name": "listenToProductOrderAttributeValueChangeEvent",
                "href": "/listener/productOrderAttributeValueChangeEvent",
                "method": "POST",
                "description": "Example of a client listener for receiving the notification ProductOrderAttributeValueChangeEvent",
            },
            {
                "name": "listenToProductOrderDeleteEvent",
                "href": "/listener/productOrderDeleteEvent",
                "method": "POST",
                "description": "Example of a client listener for receiving the notification ProductOrderDeleteEvent",
            },
            {
                "name": "listenToProductOrderStateChangeEvent",
                "href": "/listener/productOrderStateChangeEvent",
                "method": "POST",
                "description": "Example of a client listener for receiving the notification ProductOrderStateChangeEvent",
            },
            {
                "name": "listenToProductOrderInformationRequiredEvent",
                "href": "/listener/productOrderInformationRequiredEvent",
                "method": "POST",
                "description": "Example of a client listener for receiving the notification ProductOrderInformationRequiredEvent",
            },
            {
                "name": "listenToCancelProductOrderCreateEvent",
                "href": "/listener/cancelProductOrderCreateEvent",
                "method": "POST",
                "description": "Example of a client listener for receiving the notification CancelProductOrderCreateEvent",
            },
            {
                "name": "listenToCancelProductOrderStateChangeEvent",
                "href": "/listener/cancelProductOrderStateChangeEvent",
                "method": "POST",
                "description": "Example of a client listener for receiving the notification CancelProductOrderStateChangeEvent",
            },
            {
                "name": "listenToCancelProductOrderInformationRequiredEvent",
                "href": "/listener/cancelProductOrderInformationRequiredEvent",
                "method": "POST",
                "description": "Example of a client listener for receiving the notification CancelProductOrderInformationRequiredEvent",
            },
        ],
    )


@router.get("/productOrder")
async def list_product_orders(
    request: Request,
    response: Response,
    fields: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    filters = _filters_from_request(request)
    all_documents = store.list_documents("product_orders", filters=filters)
    paged_documents = all_documents[max(offset, 0): max(offset, 0) + max(limit, 0)]
    response.headers["X-Total-Count"] = str(len(all_documents))
    response.headers["X-Result-Count"] = str(len(paged_documents))
    return [_select_fields(document, fields) for document in paged_documents]


@router.post("/productOrder", status_code=status.HTTP_201_CREATED)
async def create_product_order(payload: dict[str, Any]) -> dict[str, Any]:
    validation = await _validate_order(payload)
    order_id = payload.get("id") or str(uuid4())[:8]
    order_state = payload.get("state") or ("acknowledged" if validation["valid"] else "held")
    now = utc_now()

    entity = {
        **payload,
        "id": order_id,
        "href": _href("productOrder", order_id),
        "orderDate": payload.get("orderDate", now),
        "expectedCompletionDate": payload.get("expectedCompletionDate", payload.get("requestedCompletionDate")),
        "state": order_state,
        "lastUpdate": now,
        "validationResult": validation,
        "@type": payload.get("@type", "ProductOrder"),
    }
    entity["productOrderItem"] = _prepare_order_items(payload.get("productOrderItem", []), validation["valid"])

    try:
        store.create_document("product_orders", entity)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    await _publish("ProductOrderCreateEvent", "productOrder", entity)
    if not validation["valid"]:
        await _publish("ProductOrderInformationRequiredEvent", "productOrder", entity)

    return entity


@router.get("/productOrder/{order_id}")
async def retrieve_product_order(order_id: str, fields: str | None = None) -> dict[str, Any]:
    document = store.get_document("product_orders", order_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"ProductOrder '{order_id}' not found")
    return _select_fields(document, fields)


@router.patch("/productOrder/{order_id}")
async def patch_product_order(order_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    existing = store.get_document("product_orders", order_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"ProductOrder '{order_id}' not found")

    previous_state = existing.get("state")
    updated = _merge_document(existing, patch)
    validation = await _validate_order(updated)
    if not validation["valid"]:
        updated["state"] = "held"
    updated["validationResult"] = validation
    updated["lastUpdate"] = utc_now()
    updated["@type"] = updated.get("@type", "ProductOrder")
    updated["productOrderItem"] = _prepare_order_items(updated.get("productOrderItem", []), validation["valid"])

    store.replace_document("product_orders", order_id, updated)

    await _publish("ProductOrderAttributeValueChangeEvent", "productOrder", updated)
    if previous_state != updated.get("state"):
        await _publish("ProductOrderStateChangeEvent", "productOrder", updated)
    if not validation["valid"]:
        await _publish("ProductOrderInformationRequiredEvent", "productOrder", updated)

    return updated


@router.delete("/productOrder/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_order(order_id: str) -> Response:
    existing = store.get_document("product_orders", order_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"ProductOrder '{order_id}' not found")

    store.delete_document("product_orders", order_id)
    await _publish("ProductOrderDeleteEvent", "productOrder", existing)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/cancelProductOrder")
async def list_cancel_product_orders(
    request: Request,
    response: Response,
    fields: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    filters = _filters_from_request(request)
    all_documents = store.list_documents("cancel_product_orders", filters=filters)
    paged_documents = all_documents[max(offset, 0): max(offset, 0) + max(limit, 0)]
    response.headers["X-Total-Count"] = str(len(all_documents))
    response.headers["X-Result-Count"] = str(len(paged_documents))
    return [_select_fields(document, fields) for document in paged_documents]


@router.post("/cancelProductOrder", status_code=status.HTTP_201_CREATED)
async def create_cancel_product_order(payload: dict[str, Any]) -> dict[str, Any]:
    product_order_id = ((payload.get("productOrder") or {}) or {}).get("id")
    product_order = store.get_document("product_orders", product_order_id) if product_order_id else None
    validation = await _validate_cancel_order(payload, product_order_exists=product_order is not None)
    cancellation_id = payload.get("id") or str(uuid4())[:8]
    task_state = payload.get("state") or ("done" if validation["valid"] else "terminatedWithError")
    now = utc_now()

    entity = {
        **payload,
        "id": cancellation_id,
        "href": _href("cancelProductOrder", cancellation_id),
        "state": task_state,
        "effectiveCancellationDate": payload.get("effectiveCancellationDate", now if validation["valid"] else None),
        "lastUpdate": now,
        "validationResult": validation,
        "@type": payload.get("@type", "CancelProductOrder"),
    }

    try:
        store.create_document("cancel_product_orders", entity)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if product_order and validation["valid"]:
        product_order["state"] = "cancelled"
        product_order["lastUpdate"] = now
        product_order["cancellationDate"] = now
        store.replace_document("product_orders", product_order["id"], product_order)
        await _publish("ProductOrderStateChangeEvent", "productOrder", product_order)

    await _publish("CancelProductOrderCreateEvent", "cancelProductOrder", entity)
    if validation["valid"]:
        await _publish("CancelProductOrderStateChangeEvent", "cancelProductOrder", entity)
    else:
        await _publish("CancelProductOrderInformationRequiredEvent", "cancelProductOrder", entity)

    return entity


@router.get("/cancelProductOrder/{cancellation_id}")
async def retrieve_cancel_product_order(cancellation_id: str, fields: str | None = None) -> dict[str, Any]:
    document = store.get_document("cancel_product_orders", cancellation_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"CancelProductOrder '{cancellation_id}' not found")
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


async def _receive_listener_event(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "received": True,
        "eventType": payload.get("eventType", "unknown"),
    }


for listener_path, listener_name in [
    ("/listener/productOrderCreateEvent", "listener_product_order_create"),
    ("/listener/productOrderAttributeValueChangeEvent", "listener_product_order_change"),
    ("/listener/productOrderDeleteEvent", "listener_product_order_delete"),
    ("/listener/productOrderStateChangeEvent", "listener_product_order_state"),
    ("/listener/productOrderInformationRequiredEvent", "listener_product_order_info"),
    ("/listener/cancelProductOrderCreateEvent", "listener_cancel_product_order_create"),
    ("/listener/cancelProductOrderStateChangeEvent", "listener_cancel_product_order_state"),
    ("/listener/cancelProductOrderInformationRequiredEvent", "listener_cancel_product_order_info"),
]:
    router.add_api_route(listener_path, _receive_listener_event, methods=["POST"], name=listener_name)


app.include_router(router)
