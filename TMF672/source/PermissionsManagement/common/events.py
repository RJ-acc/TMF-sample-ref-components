from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qs
from uuid import uuid4

import httpx

logger = logging.getLogger(__name__)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_event(event_type: str, resource_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "eventId": str(uuid4()),
        "eventTime": utc_now(),
        "eventType": event_type,
        "resourceType": resource_type,
        "title": event_type,
        "event": {
            resource_type: payload,
        },
    }


def subscription_matches(query: str | None, event_type: str) -> bool:
    if not query:
        return True

    parsed = parse_qs(query, keep_blank_values=True)
    values = []
    for key, raw_values in parsed.items():
        if key != "eventType":
            continue
        for raw_value in raw_values:
            values.extend([entry.strip() for entry in raw_value.split(",") if entry.strip()])

    return not values or event_type in values


async def publish_event(subscriptions: list[dict[str, Any]], event: dict[str, Any]) -> dict[str, Any]:
    delivered: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=3.0) as client:
        for subscription in subscriptions:
            callback = subscription.get("callback")
            if not callback:
                continue
            if not subscription_matches(subscription.get("query"), event["eventType"]):
                continue

            try:
                response = await client.post(callback, json=event)
                delivered.append(
                    {
                        "subscriptionId": subscription.get("id"),
                        "statusCode": response.status_code,
                        "callback": callback,
                    }
                )
            except Exception as exc:  # pragma: no cover - depends on runtime infra
                logger.warning("Event delivery failed for %s: %s", callback, exc)
                failed.append(
                    {
                        "subscriptionId": subscription.get("id"),
                        "callback": callback,
                        "error": str(exc),
                    }
                )

    return {
        "eventType": event["eventType"],
        "delivered": delivered,
        "failed": failed,
    }
