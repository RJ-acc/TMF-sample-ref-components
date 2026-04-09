from __future__ import annotations

import copy
import logging
import os
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from common.api_directory import build_api_directory
from common.configurations import evaluate_check_product_configuration, generate_query_product_configuration
from common.events import build_event, publish_event, utc_now
from common.store import get_store
from common.validation import validate_check_product_configuration, validate_query_product_configuration

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("tmfc027-product-configurator-api")

COMPONENT_NAME = os.getenv("COMPONENT_NAME", "productconfigurator")
API_BASE_PATH = "/" + os.getenv("API_BASE_PATH", "/tmf-api/productConfiguration/v5").strip("/")
ENGINE_SERVICE_URL = os.getenv("ENGINE_SERVICE_URL", "").rstrip("/")
API_VERSION = "5.0.0"
API_DIRECTORY_DESCRIPTION = """## TMF API Reference: TMF760 - Product Configuration Management

### Reference component: TMFC027 Product Configurator

Product Configuration Management API supports product configuration query capture, product configuration validity checks,
and event subscription management.

### Operations
- Retrieve an entity or a collection of entities depending on filter criteria
- Create query and check product configuration tasks
- Register and unregister event listeners
"""

LISTENER_OPERATIONS = [
    ("listenToCheckProductConfigurationAttributeValueChangeEvent", "/listener/checkProductConfigurationAttributeValueChangeEvent"),
    ("listenToCheckProductConfigurationCreateEvent", "/listener/checkProductConfigurationCreateEvent"),
    ("listenToCheckProductConfigurationDeleteEvent", "/listener/checkProductConfigurationDeleteEvent"),
    ("listenToCheckProductConfigurationStateChangeEvent", "/listener/checkProductConfigurationStateChangeEvent"),
    ("listenToQueryProductConfigurationAttributeValueChangeEvent", "/listener/queryProductConfigurationAttributeValueChangeEvent"),
    ("listenToQueryProductConfigurationCreateEvent", "/listener/queryProductConfigurationCreateEvent"),
    ("listenToQueryProductConfigurationDeleteEvent", "/listener/queryProductConfigurationDeleteEvent"),
    ("listenToQueryProductConfigurationStateChangeEvent", "/listener/queryProductConfigurationStateChangeEvent"),
]

app = FastAPI(
    title="TMFC027 Product Configurator API",
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


def _filters_from_request(request: Request) -> dict[str, Any]:
    return {
        key: value
        for key, value in request.query_params.items()
        if key not in {"fields", "offset", "limit"}
    }


def _prepare_items(items: list[dict[str, Any]] | None, item_type: str) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    prepared = []
    for index, item in enumerate(items or [], start=1):
        if not isinstance(item, dict):
            continue
        candidate = copy.deepcopy(item)
        candidate.setdefault("id", str(index))
        candidate.setdefault("@type", item_type)
        prepared.append(candidate)
    return prepared


def _entity_state(validation: dict[str, Any], payload: dict[str, Any]) -> str:
    if payload.get("state"):
        return payload["state"]
    return "done" if validation.get("valid") else "terminatedWithError"


def _response_status_code(payload: dict[str, Any]) -> int:
    return status.HTTP_200_OK if payload.get("instantSync") else status.HTTP_201_CREATED


async def _query_configuration(payload: dict[str, Any]) -> dict[str, Any]:
    if not ENGINE_SERVICE_URL:
        return generate_query_product_configuration(payload)

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(f"{ENGINE_SERVICE_URL}/configure/queryProductConfiguration", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        logger.warning("Configuration engine unavailable for query flow, using in-process fallback: %s", exc)
        return generate_query_product_configuration(payload)


async def _check_configuration(payload: dict[str, Any]) -> dict[str, Any]:
    if not ENGINE_SERVICE_URL:
        return evaluate_check_product_configuration(payload)

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(f"{ENGINE_SERVICE_URL}/check/checkProductConfiguration", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        logger.warning("Configuration engine unavailable for check flow, using in-process fallback: %s", exc)
        return evaluate_check_product_configuration(payload)


async def _publish(event_type: str, resource_type: str, payload: dict[str, Any]) -> None:
    subscriptions = store.list_documents("subscriptions")
    await publish_event(subscriptions, build_event(event_type, resource_type, payload))


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "backend": store.backend, "component": COMPONENT_NAME}


@router.get("", include_in_schema=False)
@router.get("/", include_in_schema=False)
async def describe_product_configuration_api() -> dict[str, Any]:
    operations = [
        {
            "name": "listCheckProductConfiguration",
            "href": "/checkProductConfiguration",
            "method": "GET",
            "description": "List or find CheckProductConfiguration objects",
        },
        {
            "name": "createCheckProductConfiguration",
            "href": "/checkProductConfiguration",
            "method": "POST",
            "description": "Creates a CheckProductConfiguration",
        },
        {
            "name": "retrieveCheckProductConfiguration",
            "href": "/checkProductConfiguration/{id}",
            "method": "GET",
            "description": "Retrieves a CheckProductConfiguration by ID",
        },
        {
            "name": "listQueryProductConfiguration",
            "href": "/queryProductConfiguration",
            "method": "GET",
            "description": "List or find QueryProductConfiguration objects",
        },
        {
            "name": "createQueryProductConfiguration",
            "href": "/queryProductConfiguration",
            "method": "POST",
            "description": "Creates a QueryProductConfiguration",
        },
        {
            "name": "retrieveQueryProductConfiguration",
            "href": "/queryProductConfiguration/{id}",
            "method": "GET",
            "description": "Retrieves a QueryProductConfiguration by ID",
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
        title="Product Configuration Management",
        version=API_VERSION,
        description=API_DIRECTORY_DESCRIPTION,
        operations=operations,
    )


@router.get("/queryProductConfiguration")
async def list_query_product_configurations(
    request: Request,
    response: Response,
    fields: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    filters = _filters_from_request(request)
    all_documents = store.list_documents("query_product_configurations", filters=filters)
    paged_documents = all_documents[max(offset, 0): max(offset, 0) + max(limit, 0)]
    response.headers["X-Total-Count"] = str(len(all_documents))
    response.headers["X-Result-Count"] = str(len(paged_documents))
    return [_select_fields(document, fields) for document in paged_documents]


@router.post("/queryProductConfiguration", status_code=status.HTTP_201_CREATED)
async def create_query_product_configuration(payload: dict[str, Any]) -> JSONResponse:
    query_result = await _query_configuration(payload)
    validation = query_result.get("validation") or validate_query_product_configuration(payload)
    entity_id = payload.get("id") or str(uuid4())[:8]
    entity = {
        **payload,
        "id": entity_id,
        "href": _href("queryProductConfiguration", entity_id),
        "state": _entity_state(validation, payload),
        "lastUpdate": utc_now(),
        "requestProductConfigurationItem": _prepare_items(
            payload.get("requestProductConfigurationItem"),
            "QueryProductConfigurationItem",
        ),
        "computedProductConfigurationItem": _prepare_items(
            query_result.get("computedItems"),
            "QueryProductConfigurationItem",
        ),
        "validationResult": validation,
        "processingSummary": query_result.get("summary", {}),
        "@type": payload.get("@type", "QueryProductConfiguration"),
    }

    try:
        store.create_document("query_product_configurations", entity)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    await _publish("QueryProductConfigurationCreateEvent", "queryProductConfiguration", entity)
    await _publish("QueryProductConfigurationStateChangeEvent", "queryProductConfiguration", entity)
    return JSONResponse(content=entity, status_code=_response_status_code(payload))


@router.get("/queryProductConfiguration/{entity_id}")
async def retrieve_query_product_configuration(entity_id: str, fields: str | None = None) -> dict[str, Any]:
    document = store.get_document("query_product_configurations", entity_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"QueryProductConfiguration '{entity_id}' not found")
    return _select_fields(document, fields)


@router.get("/checkProductConfiguration")
async def list_check_product_configurations(
    request: Request,
    response: Response,
    fields: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    filters = _filters_from_request(request)
    all_documents = store.list_documents("check_product_configurations", filters=filters)
    paged_documents = all_documents[max(offset, 0): max(offset, 0) + max(limit, 0)]
    response.headers["X-Total-Count"] = str(len(all_documents))
    response.headers["X-Result-Count"] = str(len(paged_documents))
    return [_select_fields(document, fields) for document in paged_documents]


@router.post("/checkProductConfiguration", status_code=status.HTTP_201_CREATED)
async def create_check_product_configuration(payload: dict[str, Any]) -> JSONResponse:
    check_result = await _check_configuration(payload)
    validation = check_result.get("validation") or validate_check_product_configuration(payload)
    entity_id = payload.get("id") or str(uuid4())[:8]
    entity = {
        **payload,
        "id": entity_id,
        "href": _href("checkProductConfiguration", entity_id),
        "state": _entity_state(validation, payload),
        "lastUpdate": utc_now(),
        "checkProductConfigurationItem": _prepare_items(
            check_result.get("checkItems"),
            "CheckProductConfigurationItem",
        ),
        "validationResult": validation,
        "processingSummary": check_result.get("summary", {}),
        "@type": payload.get("@type", "CheckProductConfiguration"),
    }

    try:
        store.create_document("check_product_configurations", entity)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    await _publish("CheckProductConfigurationCreateEvent", "checkProductConfiguration", entity)
    await _publish("CheckProductConfigurationStateChangeEvent", "checkProductConfiguration", entity)
    return JSONResponse(content=entity, status_code=_response_status_code(payload))


@router.get("/checkProductConfiguration/{entity_id}")
async def retrieve_check_product_configuration(entity_id: str, fields: str | None = None) -> dict[str, Any]:
    document = store.get_document("check_product_configurations", entity_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"CheckProductConfiguration '{entity_id}' not found")
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
