from __future__ import annotations

import os
from collections import Counter
from typing import Any

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

EVENT_COUNTER: Counter[str] = Counter()
STATE_COUNTER: Counter[str] = Counter()
API_BASE_PATH = "/" + os.getenv("API_BASE_PATH", "").strip("/")

app = FastAPI(title="TMFC030 Metrics Listener", docs_url=None, redoc_url=None)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/listener/customerBillEvent")
async def consume_event(payload: dict[str, Any]) -> dict[str, Any]:
    event_type = payload.get("eventType", "unknown")
    EVENT_COUNTER[event_type] += 1

    event_payload = payload.get("event") or {}
    for resource_name in ("customerBill", "customerBillOnDemand"):
        document = event_payload.get(resource_name)
        if not isinstance(document, dict):
            continue
        state = document.get("state")
        if state:
            STATE_COUNTER[f"{resource_name}:{state}"] += 1

    return {"accepted": True, "eventType": event_type}


def _render_metrics() -> str:
    lines = [
        "# HELP tmfc030_customer_bill_events_total TMFC030 customer bill events observed by the metrics listener",
        "# TYPE tmfc030_customer_bill_events_total counter",
    ]

    if EVENT_COUNTER:
        for event_type, count in sorted(EVENT_COUNTER.items()):
            lines.append(f'tmfc030_customer_bill_events_total{{eventType="{event_type}"}} {count}')
    else:
        lines.append('tmfc030_customer_bill_events_total{eventType="none"} 0')

    lines.extend(
        [
            "# HELP tmfc030_customer_bill_states_total TMFC030 customer bill states observed from state change events",
            "# TYPE tmfc030_customer_bill_states_total counter",
        ]
    )

    if STATE_COUNTER:
        for key, count in sorted(STATE_COUNTER.items()):
            resource_name, state = key.split(":", 1)
            lines.append(
                f'tmfc030_customer_bill_states_total{{resource="{resource_name}",state="{state}"}} {count}'
            )
    else:
        lines.append('tmfc030_customer_bill_states_total{resource="none",state="none"} 0')

    return "\n".join(lines) + "\n"


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> str:
    return _render_metrics()


if API_BASE_PATH != "/":
    @app.get(f"{API_BASE_PATH}/metrics", response_class=PlainTextResponse)
    async def metrics_with_base_path() -> str:
        return _render_metrics()
