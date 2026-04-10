from __future__ import annotations

import logging
import os
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, FastAPI, HTTPException, Request, Response, status

from common.api_directory import build_api_directory
from common.events import build_event, publish_event
from common.sla import (
    LISTENER_EVENT_SUFFIXES,
    apply_patch as apply_sla_patch,
    apply_replace,
    build_entity,
    ensure_seed_data,
    resource_collection,
    resource_names,
    resource_type,
)
from common.store import get_store
from common.validation import validate_create_payload, validate_patch_payload, validate_replace_payload

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("tmf623-sla-management-api")

COMPONENT_NAME = os.getenv("COMPONENT_NAME", "slamanagement")
API_BASE_PATH = "/" + os.getenv("API_BASE_PATH", "/tmf-api/slaManagement/v2").strip("/")
ENGINE_SERVICE_URL = os.getenv("ENGINE_SERVICE_URL", "").rstrip("/")
API_VERSION = "2.0.0"
API_DIRECTORY_DESCRIPTION = """## TMF API Reference: TMF623 - SLA Management

### Reference component: TMF623 SLA Management

SLA Management exposes the TMF623 resources:
sla and slaViolation.

### Operations
- List, create, retrieve, delete, replace, and patch SLA and SLAViolation records
- List, create, retrieve, and delete hub subscriptions
- Accept TMF623 listener callbacks for create, delete, state-change, and attribute-value-change events
"""

app = FastAPI(
    title="TMF623 SLA Management API",
    docs_url=f"{API_BASE_PATH}/docs",
    openapi_url=f"{API_BASE_PATH}/openapi.json",
)
router = APIRouter(prefix=API_BASE_PATH)
store = get_store()


def _seed() -> None:
    ensure_seed_data(store, base_path=API_BASE_PATH)


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


def _listener_operations() -> list[tuple[str, str]]:
    operations: list[tuple[str, str]] = []
    for resource_name in resource_names():
        entity_type = resource_type(resource_name)
        for suffix in LISTENER_EVENT_SUFFIXES:
            operations.append((f"listenTo{entity_type}{suffix}", f"/listener/{resource_name}{suffix}"))
    return operations


LISTENER_OPERATIONS = _listener_operations()


async def _validate_with_engine(
    resource_name: str,
    payload: dict[str, Any],
    *,
    mode: str,
) -> dict[str, Any]:
    if mode == "patch":
        fallback = validate_patch_payload(resource_name, payload)
        path = f"/validate/{resource_name}/patch"
    elif mode == "replace":
        fallback = validate_replace_payload(resource_name, payload)
        path = f"/validate/{resource_name}/replace"
    else:
        fallback = validate_create_payload(resource_name, payload)
        path = f"/validate/{resource_name}"

    if not ENGINE_SERVICE_URL:
        return fallback

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(f"{ENGINE_SERVICE_URL}{path}", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        logger.warning("Engine validation unavailable for %s %s, using in-process fallback: %s", resource_name, path, exc)
        return fallback


async def _publish_event(resource_name: str, suffix: str, payload: dict[str, Any]) -> None:
    subscriptions = store.list_documents("subscriptions")
    event_type = f"{resource_type(resource_name)}{suffix}"
    await publish_event(subscriptions, build_event(event_type, resource_name, payload))


@app.get("/health")
async def health() -> dict[str, Any]:
    _seed()
    return {"status": "ok", "backend": store.backend, "component": COMPONENT_NAME}


@router.get("", include_in_schema=False)
@router.get("/", include_in_schema=False)
async def describe_sla_api() -> dict[str, Any]:
    operations: list[dict[str, str]] = []

    for resource_name in resource_names():
        entity_type = resource_type(resource_name)
        operations.extend(
            [
                {
                    "name": f"list{entity_type}",
                    "href": f"/{resource_name}",
                    "method": "GET",
                    "description": f"List or find {entity_type} objects",
                },
                {
                    "name": f"create{entity_type}",
                    "href": f"/{resource_name}",
                    "method": "POST",
                    "description": f"Creates a {entity_type} entity",
                },
                {
                    "name": f"retrieve{entity_type}",
                    "href": f"/{resource_name}/{{id}}",
                    "method": "GET",
                    "description": f"Retrieves a {entity_type} by ID",
                },
                {
                    "name": f"delete{entity_type}",
                    "href": f"/{resource_name}/{{id}}",
                    "method": "DELETE",
                    "description": f"Deletes a {entity_type} entity",
                },
                {
                    "name": f"replace{entity_type}",
                    "href": f"/{resource_name}/{{id}}",
                    "method": "PUT",
                    "description": f"Replaces a {entity_type} entity",
                },
                {
                    "name": f"patch{entity_type}",
                    "href": f"/{resource_name}/{{id}}",
                    "method": "PATCH",
                    "description": f"Updates partially a {entity_type} entity",
                },
            ]
        )

    operations.extend(
        [
            {
                "name": "listHub",
                "href": "/hub",
                "method": "GET",
                "description": "List registered event subscriptions",
            },
            {
                "name": "registerListener",
                "href": "/hub",
                "method": "POST",
                "description": "Create a subscription (hub) to receive Events",
            },
            {
                "name": "retrieveListener",
                "href": "/hub/{id}",
                "method": "GET",
                "description": "Retrieve a subscription (hub) by id",
            },
            {
                "name": "unregisterListener",
                "href": "/hub/{id}",
                "method": "DELETE",
                "description": "Remove a subscription (hub) to receive Events",
            },
        ]
    )
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
        title="SLA Management",
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


def _list_handler(resource_name: str):
    collection = resource_collection(resource_name)

    async def handler(
        request: Request,
        response: Response,
        fields: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        _seed()
        return _paged_documents(collection, request, response, fields, offset, limit)

    handler.__name__ = f"list_{resource_name}"
    return handler


def _create_handler(resource_name: str):
    collection = resource_collection(resource_name)

    async def handler(payload: dict[str, Any]) -> dict[str, Any]:
        _seed()
        validation = await _validate_with_engine(resource_name, payload, mode="create")
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=validation)

        entity = build_entity(resource_name, payload, API_BASE_PATH)
        try:
            store.create_document(collection, entity)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

        await _publish_event(resource_name, "CreateEvent", entity)
        return entity

    handler.__name__ = f"create_{resource_name}"
    return handler


def _retrieve_handler(resource_name: str):
    collection = resource_collection(resource_name)
    entity_type = resource_type(resource_name)

    async def handler(entity_id: str, fields: str | None = None) -> dict[str, Any]:
        _seed()
        document = store.get_document(collection, entity_id)
        if not document:
            raise HTTPException(status_code=404, detail=f"{entity_type} '{entity_id}' not found")
        return _select_fields(document, fields)

    handler.__name__ = f"retrieve_{resource_name}"
    return handler


def _delete_handler(resource_name: str):
    collection = resource_collection(resource_name)
    entity_type = resource_type(resource_name)

    async def handler(entity_id: str) -> Response:
        _seed()
        existing = store.get_document(collection, entity_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"{entity_type} '{entity_id}' not found")

        store.delete_document(collection, entity_id)
        await _publish_event(resource_name, "DeleteEvent", existing)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    handler.__name__ = f"delete_{resource_name}"
    return handler


def _replace_handler(resource_name: str):
    collection = resource_collection(resource_name)
    entity_type = resource_type(resource_name)

    async def handler(entity_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        _seed()
        existing = store.get_document(collection, entity_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"{entity_type} '{entity_id}' not found")

        validation = await _validate_with_engine(resource_name, payload, mode="replace")
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=validation)

        updated = apply_replace(resource_name, existing, payload, API_BASE_PATH)
        store.replace_document(collection, entity_id, updated)
        await _publish_event(resource_name, "AttributeValueChangeEvent", updated)
        if updated.get("state") != existing.get("state"):
            await _publish_event(resource_name, "StateChangeEvent", updated)
        return updated

    handler.__name__ = f"replace_{resource_name}"
    return handler


def _patch_handler(resource_name: str):
    collection = resource_collection(resource_name)
    entity_type = resource_type(resource_name)

    async def handler(entity_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        _seed()
        existing = store.get_document(collection, entity_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"{entity_type} '{entity_id}' not found")

        validation = await _validate_with_engine(resource_name, patch, mode="patch")
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=validation)

        updated = apply_sla_patch(resource_name, existing, patch, API_BASE_PATH)
        store.replace_document(collection, entity_id, updated)
        await _publish_event(resource_name, "AttributeValueChangeEvent", updated)
        if updated.get("state") != existing.get("state"):
            await _publish_event(resource_name, "StateChangeEvent", updated)
        return updated

    handler.__name__ = f"patch_{resource_name}"
    return handler


for resource_name in resource_names():
    router.add_api_route(f"/{resource_name}", _list_handler(resource_name), methods=["GET"], name=f"list_{resource_name}")
    router.add_api_route(
        f"/{resource_name}",
        _create_handler(resource_name),
        methods=["POST"],
        name=f"create_{resource_name}",
        status_code=status.HTTP_201_CREATED,
    )
    router.add_api_route(
        f"/{resource_name}/{{entity_id}}",
        _retrieve_handler(resource_name),
        methods=["GET"],
        name=f"retrieve_{resource_name}",
    )
    router.add_api_route(
        f"/{resource_name}/{{entity_id}}",
        _delete_handler(resource_name),
        methods=["DELETE"],
        name=f"delete_{resource_name}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    router.add_api_route(
        f"/{resource_name}/{{entity_id}}",
        _replace_handler(resource_name),
        methods=["PUT"],
        name=f"replace_{resource_name}",
    )
    router.add_api_route(
        f"/{resource_name}/{{entity_id}}",
        _patch_handler(resource_name),
        methods=["PATCH"],
        name=f"patch_{resource_name}",
    )


@router.get("/hub")
async def list_listeners(
    request: Request,
    response: Response,
    fields: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    _seed()
    return _paged_documents("subscriptions", request, response, fields, offset, limit)


@router.post("/hub", status_code=status.HTTP_201_CREATED)
async def register_listener(payload: dict[str, Any]) -> dict[str, Any]:
    _seed()
    callback = payload.get("callback")
    if not callback:
        raise HTTPException(status_code=400, detail="callback is required")

    query = payload.get("query", "")
    existing = next(
        (
            subscription
            for subscription in store.list_documents("subscriptions")
            if subscription.get("callback") == callback and subscription.get("query", "") == query
        ),
        None,
    )
    if existing:
        return existing

    entity_id = payload.get("id") or str(uuid4())
    entity = {
        "id": entity_id,
        "callback": callback,
        "query": query,
        "href": f"{API_BASE_PATH}/hub/{entity_id}",
        "@type": payload.get("@type", "EventSubscription"),
    }
    try:
        store.create_document("subscriptions", entity)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return entity


@router.get("/hub/{subscription_id}")
async def retrieve_listener(subscription_id: str, fields: str | None = None) -> dict[str, Any]:
    _seed()
    document = store.get_document("subscriptions", subscription_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Subscription '{subscription_id}' not found")
    return _select_fields(document, fields)


@router.delete("/hub/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_listener(subscription_id: str) -> Response:
    deleted = store.delete_document("subscriptions", subscription_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Subscription '{subscription_id}' not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _listener_handler(listener_path: str):
    async def handler(payload: dict[str, Any]) -> Response:
        logger.info("Received listener callback for %s: %s", listener_path, payload.get("eventType"))
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    handler.__name__ = "listener_" + listener_path.strip("/").replace("/", "_")
    return handler


for _, listener_path in LISTENER_OPERATIONS:
    router.add_api_route(
        listener_path,
        _listener_handler(listener_path),
        methods=["POST"],
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )


app.include_router(router)
