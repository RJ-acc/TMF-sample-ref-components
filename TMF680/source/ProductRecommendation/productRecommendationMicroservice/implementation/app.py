from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, FastAPI, HTTPException, Request, Response, status

from common.api_directory import build_api_directory
from common.events import build_event, publish_event, utc_now
from common.recommendations import generate_recommendations
from common.store import get_store
from common.validation import validate_query_product_recommendation

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("tmfc050-product-recommendation-api")

COMPONENT_NAME = os.getenv("COMPONENT_NAME", "productrecommendation")
API_BASE_PATH = "/" + os.getenv("API_BASE_PATH", "/tmf-api/recommendationManagement/v4").strip("/")
ENGINE_SERVICE_URL = os.getenv("ENGINE_SERVICE_URL", "").rstrip("/")
API_VERSION = "4.0.0"
API_DIRECTORY_DESCRIPTION = """## TMF API Reference: TMF680 - Recommendation

### Reference component: TMFC050 Product Recommendation

Recommendation API supports recommendation query capture, deterministic recommendation generation,
and event subscription management.

### Operations
- Retrieve an entity or a collection of entities depending on filter criteria
- Create a recommendation query
- Register and unregister event listeners
"""

app = FastAPI(
    title="TMFC050 Product Recommendation API",
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


def _prepare_recommendation_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prepared = []
    for index, item in enumerate(items or [], start=1):
        candidate = dict(item)
        candidate.setdefault("id", candidate.get("productOffering", {}).get("id", str(index)))
        candidate.setdefault("priority", index)
        candidate.setdefault("@type", "RecommendationItem")
        prepared.append(candidate)
    return prepared


def _default_valid_for() -> dict[str, str]:
    start = datetime.now(timezone.utc)
    end = start + timedelta(days=7)
    return {
        "startDateTime": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "endDateTime": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


async def _recommend(payload: dict[str, Any]) -> dict[str, Any]:
    if not ENGINE_SERVICE_URL:
        return generate_recommendations(payload)

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(f"{ENGINE_SERVICE_URL}/recommend/queryProductRecommendation", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        logger.warning("Recommendation engine unavailable, falling back to in-process generation: %s", exc)
        return generate_recommendations(payload)


async def _publish(event_type: str, resource_type: str, payload: dict[str, Any]) -> None:
    subscriptions = store.list_documents("subscriptions")
    await publish_event(subscriptions, build_event(event_type, resource_type, payload))


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "backend": store.backend, "component": COMPONENT_NAME}


@router.get("", include_in_schema=False)
@router.get("/", include_in_schema=False)
async def describe_recommendation_api() -> dict[str, Any]:
    return build_api_directory(
        base_path=API_BASE_PATH,
        title="Recommendation Management",
        version=API_VERSION,
        description=API_DIRECTORY_DESCRIPTION,
        operations=[
            {
                "name": "listQueryProductRecommendation",
                "href": "/queryProductRecommendation",
                "method": "GET",
                "description": "This operation list or find QueryProductRecommendation entities",
            },
            {
                "name": "createQueryProductRecommendation",
                "href": "/queryProductRecommendation",
                "method": "POST",
                "description": "This operation creates a QueryProductRecommendation entity.",
            },
            {
                "name": "retrieveQueryProductRecommendation",
                "href": "/queryProductRecommendation/{id}",
                "method": "GET",
                "description": "This operation retrieves a QueryProductRecommendation entity. Attribute selection is enabled for all first level attributes.",
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
                "name": "listenToQueryProductRecommendationCreateEvent",
                "href": "/listener/queryProductRecommendationCreateEvent",
                "method": "POST",
                "description": "Example of a client listener for receiving the notification QueryProductRecommendationCreateEvent",
            },
            {
                "name": "listenToQueryProductRecommendationStateChangeEvent",
                "href": "/listener/queryProductRecommendationStateChangeEvent",
                "method": "POST",
                "description": "Example of a client listener for receiving the notification QueryProductRecommendationStateChangeEvent",
            },
        ],
    )


@router.get("/queryProductRecommendation")
async def list_query_product_recommendations(
    request: Request,
    response: Response,
    fields: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    filters = _filters_from_request(request)
    all_documents = store.list_documents("query_product_recommendations", filters=filters)
    paged_documents = all_documents[max(offset, 0): max(offset, 0) + max(limit, 0)]
    response.headers["X-Total-Count"] = str(len(all_documents))
    response.headers["X-Result-Count"] = str(len(paged_documents))
    return [_select_fields(document, fields) for document in paged_documents]


@router.post("/queryProductRecommendation", status_code=status.HTTP_201_CREATED)
async def create_query_product_recommendation(payload: dict[str, Any]) -> dict[str, Any]:
    recommendation_result = await _recommend(payload)
    validation = recommendation_result.get("validation") or validate_query_product_recommendation(payload)
    recommendation_id = payload.get("id") or str(uuid4())[:8]
    now = utc_now()
    recommendation_items = payload.get("recommendationItem") or recommendation_result.get("recommendationItems", [])

    entity = {
        **payload,
        "id": recommendation_id,
        "href": _href("queryProductRecommendation", recommendation_id),
        "state": payload.get("state", "done" if validation["valid"] else "terminatedWithError"),
        "lastUpdate": now,
        "validFor": payload.get("validFor", _default_valid_for()),
        "recommendationItem": _prepare_recommendation_items(recommendation_items),
        "validationResult": validation,
        "generationSummary": recommendation_result.get("summary", {}),
        "@type": payload.get("@type", "QueryProductRecommendation"),
    }

    try:
        store.create_document("query_product_recommendations", entity)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    await _publish("QueryProductRecommendationCreateEvent", "queryProductRecommendation", entity)
    await _publish("QueryProductRecommendationStateChangeEvent", "queryProductRecommendation", entity)
    return entity


@router.get("/queryProductRecommendation/{recommendation_id}")
async def retrieve_query_product_recommendation(
    recommendation_id: str,
    fields: str | None = None,
) -> dict[str, Any]:
    document = store.get_document("query_product_recommendations", recommendation_id)
    if not document:
        raise HTTPException(
            status_code=404,
            detail=f"QueryProductRecommendation '{recommendation_id}' not found",
        )
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
    ("/listener/queryProductRecommendationCreateEvent", "listener_query_product_recommendation_create"),
    ("/listener/queryProductRecommendationStateChangeEvent", "listener_query_product_recommendation_state"),
]:
    router.add_api_route(listener_path, _receive_listener_event, methods=["POST"], name=listener_name)


app.include_router(router)
