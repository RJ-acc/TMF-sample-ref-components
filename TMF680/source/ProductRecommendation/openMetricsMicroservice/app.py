from __future__ import annotations

import os
from collections import defaultdict
from typing import Any

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI(title="TMFC050 Metrics Listener", docs_url=None, redoc_url=None)
API_BASE_PATH = "/" + os.getenv("API_BASE_PATH", "").strip("/")
event_counts: defaultdict[tuple[str, str], int] = defaultdict(int)
state_counts: defaultdict[str, int] = defaultdict(int)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/listener/recommendationEvent")
async def receive_recommendation_event(payload: dict[str, Any]) -> dict[str, Any]:
    event_type = payload.get("eventType", "UnknownEvent")
    resource_type = payload.get("resourceType", "unknown")
    event_counts[(event_type, resource_type)] += 1
    if event_type.endswith("StateChangeEvent"):
        state = ((payload.get("event") or {}).get(resource_type) or {}).get("state", "unknown")
        state_counts[state] += 1
    return {
        "received": True,
        "eventType": event_type,
        "resourceType": resource_type,
    }


def _render_metrics() -> PlainTextResponse:
    lines = [
        "# HELP tmfc050_recommendation_events_total TMFC050 recommendation events observed by the metrics listener",
        "# TYPE tmfc050_recommendation_events_total counter",
    ]
    for (event_type, resource_type), count in sorted(event_counts.items()):
        lines.append(
            f'tmfc050_recommendation_events_total{{event_type="{event_type}",resource_type="{resource_type}"}} {count}'
        )

    lines.extend(
        [
            "# HELP tmfc050_recommendation_states_total TMFC050 recommendation states observed from state change events",
            "# TYPE tmfc050_recommendation_states_total counter",
        ]
    )
    for state, count in sorted(state_counts.items()):
        lines.append(f'tmfc050_recommendation_states_total{{state="{state}"}} {count}')

    return PlainTextResponse("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    return _render_metrics()


if API_BASE_PATH != "/":
    @app.get(f"{API_BASE_PATH}/metrics")
    async def metrics_with_base_path() -> PlainTextResponse:
        return _render_metrics()
