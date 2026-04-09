from __future__ import annotations

import os
from collections import Counter
from typing import Any

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

EVENT_COUNTER: Counter[str] = Counter()
STATUS_COUNTER: Counter[str] = Counter()
API_BASE_PATH = "/" + os.getenv("API_BASE_PATH", "").strip("/")

app = FastAPI(title="TMFC005 Metrics Listener", docs_url=None, redoc_url=None)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/listener/productEvent")
async def consume_event(payload: dict[str, Any]) -> dict[str, Any]:
    event_type = payload.get("eventType", "unknown")
    resource_type = payload.get("resourceType", "unknown")
    EVENT_COUNTER[f"{resource_type}:{event_type}"] += 1

    event_payload = payload.get("event") or {}
    resource_document = event_payload.get(resource_type)
    if isinstance(resource_document, dict):
        status = resource_document.get("status")
        if status:
            STATUS_COUNTER[f"{resource_type}:{status}"] += 1

    return {"accepted": True, "eventType": event_type}


def _render_metrics() -> str:
    lines = [
        "# HELP tmfc005_product_inventory_events_total TMFC005 product inventory events observed by the metrics listener",
        "# TYPE tmfc005_product_inventory_events_total counter",
    ]

    if EVENT_COUNTER:
        for key, count in sorted(EVENT_COUNTER.items()):
            resource_type, event_type = key.split(":", 1)
            lines.append(
                f'tmfc005_product_inventory_events_total{{resource="{resource_type}",eventType="{event_type}"}} {count}'
            )
    else:
        lines.append('tmfc005_product_inventory_events_total{resource="none",eventType="none"} 0')

    lines.extend(
        [
            "# HELP tmfc005_product_inventory_status_total TMFC005 product statuses observed from incoming events",
            "# TYPE tmfc005_product_inventory_status_total counter",
        ]
    )

    if STATUS_COUNTER:
        for key, count in sorted(STATUS_COUNTER.items()):
            resource_type, status = key.split(":", 1)
            lines.append(f'tmfc005_product_inventory_status_total{{resource="{resource_type}",status="{status}"}} {count}')
    else:
        lines.append('tmfc005_product_inventory_status_total{resource="none",status="none"} 0')

    return "\n".join(lines) + "\n"


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> str:
    return _render_metrics()


if API_BASE_PATH != "/":
    @app.get(f"{API_BASE_PATH}/metrics", response_class=PlainTextResponse)
    async def metrics_with_base_path() -> str:
        return _render_metrics()
