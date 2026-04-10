from __future__ import annotations

import os
from collections import Counter
from typing import Any

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

EVENT_COUNTER: Counter[str] = Counter()
STATE_COUNTER: Counter[str] = Counter()
SEVERITY_COUNTER: Counter[str] = Counter()
API_BASE_PATH = "/" + os.getenv("API_BASE_PATH", "").strip("/")

app = FastAPI(title="TMF623 Metrics Listener", docs_url=None, redoc_url=None)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/listener/slaEvent")
async def consume_event(payload: dict[str, Any]) -> dict[str, Any]:
    event_type = payload.get("eventType", "unknown")
    resource_type = payload.get("resourceType", "unknown")
    EVENT_COUNTER[f"{resource_type}:{event_type}"] += 1

    event_payload = payload.get("event") or {}
    resource_document = event_payload.get(resource_type)
    if isinstance(resource_document, dict):
        state = resource_document.get("state")
        if state:
            STATE_COUNTER[f"{resource_type}:{state}"] += 1
        severity = resource_document.get("severity")
        if severity:
            SEVERITY_COUNTER[f"{resource_type}:{severity}"] += 1

    return {"accepted": True, "eventType": event_type}


def _render_metrics() -> str:
    lines = [
        "# HELP tmf623_sla_events_total TMF623 SLA-management events observed by the metrics listener",
        "# TYPE tmf623_sla_events_total counter",
    ]

    if EVENT_COUNTER:
        for key, count in sorted(EVENT_COUNTER.items()):
            resource_type, event_type = key.split(":", 1)
            lines.append(f'tmf623_sla_events_total{{resource="{resource_type}",eventType="{event_type}"}} {count}')
    else:
        lines.append('tmf623_sla_events_total{resource="none",eventType="none"} 0')

    lines.extend(
        [
            "# HELP tmf623_sla_states_total TMF623 SLA states observed from incoming events",
            "# TYPE tmf623_sla_states_total counter",
        ]
    )

    if STATE_COUNTER:
        for key, count in sorted(STATE_COUNTER.items()):
            resource_type, state = key.split(":", 1)
            lines.append(f'tmf623_sla_states_total{{resource="{resource_type}",state="{state}"}} {count}')
    else:
        lines.append('tmf623_sla_states_total{resource="none",state="none"} 0')

    lines.extend(
        [
            "# HELP tmf623_sla_violation_severity_total TMF623 SLA violation severities observed from incoming events",
            "# TYPE tmf623_sla_violation_severity_total counter",
        ]
    )

    if SEVERITY_COUNTER:
        for key, count in sorted(SEVERITY_COUNTER.items()):
            resource_type, severity = key.split(":", 1)
            lines.append(
                f'tmf623_sla_violation_severity_total{{resource="{resource_type}",severity="{severity}"}} {count}'
            )
    else:
        lines.append('tmf623_sla_violation_severity_total{resource="none",severity="none"} 0')

    return "\n".join(lines) + "\n"


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> str:
    return _render_metrics()


if API_BASE_PATH != "/":
    @app.get(f"{API_BASE_PATH}/metrics", response_class=PlainTextResponse)
    async def metrics_with_base_path() -> str:
        return _render_metrics()
