from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, generate_latest

app = FastAPI(title="TMFC002 Metrics Listener", docs_url=None, redoc_url=None)
API_BASE_PATH = "/" + os.getenv("API_BASE_PATH", "").strip("/")
registry = CollectorRegistry()
event_counter = Counter(
    "tmfc002_order_events_total",
    "TMFC002 order events observed by the metrics listener",
    ["event_type", "resource_type"],
    registry=registry,
)
information_required_counter = Counter(
    "tmfc002_information_required_total",
    "TMFC002 information-required events observed by the metrics listener",
    ["resource_type"],
    registry=registry,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/listener/orderEvent")
async def receive_order_event(payload: dict[str, Any]) -> dict[str, Any]:
    event_type = payload.get("eventType", "UnknownEvent")
    resource_type = payload.get("resourceType", "unknown")
    event_counter.labels(event_type=event_type, resource_type=resource_type).inc()
    if event_type.endswith("InformationRequiredEvent"):
        information_required_counter.labels(resource_type=resource_type).inc()
    return {
        "received": True,
        "eventType": event_type,
        "resourceType": resource_type,
    }


def _render_metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest(registry).decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    return _render_metrics()


if API_BASE_PATH != "/":
    @app.get(f"{API_BASE_PATH}/metrics")
    async def metrics_with_base_path() -> PlainTextResponse:
        return _render_metrics()
