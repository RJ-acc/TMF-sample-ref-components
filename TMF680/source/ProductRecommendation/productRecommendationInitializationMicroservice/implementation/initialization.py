from __future__ import annotations

import os
import sys
import time

import httpx

EVENT_TYPES = [
    "QueryProductRecommendationCreateEvent",
    "QueryProductRecommendationStateChangeEvent",
]


def main() -> int:
    base_url = os.getenv(
        "RECOMMENDATION_API_BASE_URL",
        "http://localhost:8080/tmf-api/recommendationManagement/v4",
    ).rstrip("/")
    metrics_callback = os.getenv("METRICS_CALLBACK_URL", "http://localhost:4000/listener/recommendationEvent")
    payload = {
        "callback": metrics_callback,
        "query": f"eventType={','.join(EVENT_TYPES)}",
        "@type": "EventSubscription",
    }

    with httpx.Client(timeout=5.0) as client:
        for attempt in range(1, 11):
            try:
                response = client.post(f"{base_url}/hub", json=payload)
                response.raise_for_status()
                print(f"Registered metrics listener at {metrics_callback}")
                return 0
            except Exception as exc:
                print(f"Product recommendation initialization attempt {attempt} failed: {exc}")
                time.sleep(3)

    print("Product recommendation initialization failed after retries", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
