from __future__ import annotations

import os
from collections import defaultdict
from typing import Any

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI(title="TMFC027 Metrics Listener", docs_url=None, redoc_url=None)
API_BASE_PATH = "/" + os.getenv("API_BASE_PATH", "").strip("/")
event_counts: defaultdict[tuple[str, str], int] = defaultdict(int)
state_counts: defaultdict[tuple[str, str], int] = defaultdict(int)


def _extract_resource_document(payload: dict[str, Any], resource_type: str) -> dict[str, Any]:
    event = payload.get("event")
    if not isinstance(event, dict):
        return {}
    if resource_type in event and isinstance(event[resource_type], dict):
        return event[resource_type]
    for value in event.values():
        if isinstance(value, dict):
            return value
    return {}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/listener/productConfigurationEvent")
async def receive_product_configuration_event(payload: dict[str, Any]) -> dict[str, Any]:
    event_type = payload.get("eventType", "UnknownEvent")
    resource_type = payload.get("resourceType", "unknown")
    event_counts[(event_type, resource_type)] += 1
    if event_type.endswith("StateChangeEvent"):
        state = _extract_resource_document(payload, resource_type).get("state", "unknown")
        state_counts[(resource_type, state)] += 1
    return {
        "received": True,
        "eventType": event_type,
        "resourceType": resource_type,
    }


def _render_metrics() -> PlainTextResponse:
    lines = [
        "# HELP tmfc027_product_configuration_events_total TMFC027 product configuration events observed by the metrics listener",
        "# TYPE tmfc027_product_configuration_events_total counter",
    ]
    for (event_type, resource_type), count in sorted(event_counts.items()):
        lines.append(
            f'tmfc027_product_configuration_events_total{{event_type="{event_type}",resource_type="{resource_type}"}} {count}'
        )

    lines.extend(
        [
            "# HELP tmfc027_product_configuration_states_total TMFC027 product configuration states observed from state change events",
            "# TYPE tmfc027_product_configuration_states_total counter",
        ]
    )
    for (resource_type, state), count in sorted(state_counts.items()):
        lines.append(
            f'tmfc027_product_configuration_states_total{{resource_type="{resource_type}",state="{state}"}} {count}'
        )

    return PlainTextResponse("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    return _render_metrics()


if API_BASE_PATH != "/":
    @app.get(f"{API_BASE_PATH}/metrics")
    async def metrics_with_base_path() -> PlainTextResponse:
        return _render_metrics()
