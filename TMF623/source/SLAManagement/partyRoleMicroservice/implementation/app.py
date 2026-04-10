from __future__ import annotations

import logging
import os
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, FastAPI, HTTPException, Request, Response, status

from common.api_directory import build_api_directory
from common.events import utc_now
from common.store import get_store

API_BASE_PATH = "/" + os.getenv("API_BASE_PATH", "/tmf-api/partyRoleManagement/v4").strip("/")
API_VERSION = "4.0.0"
API_DIRECTORY_DESCRIPTION = """## TMF API Reference: TMF669 - Party Role Management

### Reference component: TMF623 SLA Management

Party Role Management API manages the component roles used by the SLA-management function.

### Operations
- Retrieve an entity or a collection of entities depending on filter criteria
- Create a party role
- Partially update an entity
- Delete an entity
"""
app = FastAPI(
    title="TMF623 Party Role API",
    docs_url=f"{API_BASE_PATH}/docs",
    openapi_url=f"{API_BASE_PATH}/openapi.json",
)
router = APIRouter(prefix=API_BASE_PATH)
store = get_store()
logger = logging.getLogger(__name__)
LISTENER_OPERATIONS = [
    ("listenToPartyRoleAttributeValueChangeEvent", "/listener/partyRoleAttributeValueChangeEvent"),
    ("listenToPartyRoleCreateEvent", "/listener/partyRoleCreateEvent"),
    ("listenToPartyRoleDeleteEvent", "/listener/partyRoleDeleteEvent"),
    ("listenToPartyRoleStateChangeEvent", "/listener/partyRoleStateChangeEvent"),
]


def _href(role_id: str) -> str:
    return f"{API_BASE_PATH}/partyRole/{role_id}"


def _select_fields(document: dict[str, Any], fields: str | None) -> dict[str, Any]:
    if not fields:
        return document
    selected = {}
    for field_name in [field.strip() for field in fields.split(",") if field.strip()]:
        if field_name in document:
            selected[field_name] = document[field_name]
    return selected


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "backend": store.backend}


@router.get("", include_in_schema=False)
@router.get("/", include_in_schema=False)
async def describe_party_role_api() -> dict[str, Any]:
    return build_api_directory(
        base_path=API_BASE_PATH,
        title="Party Role Management",
        version=API_VERSION,
        description=API_DIRECTORY_DESCRIPTION,
        operations=[
            {
                "name": "listPartyRole",
                "href": "/partyRole",
                "method": "GET",
                "description": "This operation list or find PartyRole entities",
            },
            {
                "name": "createPartyRole",
                "href": "/partyRole",
                "method": "POST",
                "description": "This operation creates a PartyRole entity.",
            },
            {
                "name": "retrievePartyRole",
                "href": "/partyRole/{id}",
                "method": "GET",
                "description": "This operation retrieves a PartyRole entity. Attribute selection is enabled for all first level attributes.",
            },
            {
                "name": "patchPartyRole",
                "href": "/partyRole/{id}",
                "method": "PATCH",
                "description": "This operation updates partially a PartyRole entity.",
            },
            {
                "name": "deletePartyRole",
                "href": "/partyRole/{id}",
                "method": "DELETE",
                "description": "This operation deletes a PartyRole entity.",
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
        ],
    )


@router.get("/partyRole")
async def list_party_roles(
    request: Request,
    response: Response,
    fields: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    filters = {
        key: value
        for key, value in request.query_params.items()
        if key not in {"fields", "offset", "limit"}
    }
    all_documents = store.list_documents("party_roles", filters=filters)
    paged_documents = all_documents[max(offset, 0): max(offset, 0) + max(limit, 0)]
    response.headers["X-Total-Count"] = str(len(all_documents))
    response.headers["X-Result-Count"] = str(len(paged_documents))
    return [_select_fields(document, fields) for document in paged_documents]


@router.post("/partyRole", status_code=status.HTTP_201_CREATED)
async def create_party_role(payload: dict[str, Any]) -> dict[str, Any]:
    role_id = payload.get("id") or str(uuid4())[:8]
    entity = {
        **payload,
        "id": role_id,
        "href": _href(role_id),
        "state": payload.get("state", "active"),
        "lastUpdate": utc_now(),
        "@type": payload.get("@type", "PartyRole"),
    }
    try:
        store.create_document("party_roles", entity)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return entity


@router.get("/partyRole/{role_id}")
async def retrieve_party_role(role_id: str, fields: str | None = None) -> dict[str, Any]:
    document = store.get_document("party_roles", role_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"PartyRole '{role_id}' not found")
    return _select_fields(document, fields)


@router.patch("/partyRole/{role_id}")
async def patch_party_role(role_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    existing = store.get_document("party_roles", role_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"PartyRole '{role_id}' not found")

    updated = {**existing, **patch, "id": role_id, "href": _href(role_id), "lastUpdate": utc_now()}
    updated["@type"] = updated.get("@type", "PartyRole")
    store.replace_document("party_roles", role_id, updated)
    return updated


@router.delete("/partyRole/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_party_role(role_id: str) -> Response:
    deleted = store.delete_document("party_roles", role_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"PartyRole '{role_id}' not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
        "href": f"{API_BASE_PATH}/hub/{subscription_id}",
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
    logger.info("Received party-role listener payload with keys: %s", sorted(payload.keys()))
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
