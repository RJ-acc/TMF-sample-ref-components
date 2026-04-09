from __future__ import annotations

import os
import sys
import time

import httpx

from common.parties import listener_event_types


def main() -> int:
    base_url = os.getenv(
        "PARTY_API_BASE_URL",
        "http://localhost:8080/tmf-api/partyManagement/v5",
    ).rstrip("/")
    metrics_callback = os.getenv("METRICS_CALLBACK_URL", "http://localhost:4000/listener/partyEvent")
    payload = {"callback": metrics_callback, "query": "eventType=" + ",".join(listener_event_types())}

    with httpx.Client(timeout=5.0) as client:
        for attempt in range(1, 11):
            try:
                response = client.post(f"{base_url}/hub", json=payload)
                response.raise_for_status()
                print(f"Registered metrics listener at {metrics_callback}")
                return 0
            except Exception as exc:
                print(f"Party-management initialization attempt {attempt} failed: {exc}")
                time.sleep(3)

    print("Party-management initialization failed after retries", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
