from __future__ import annotations

import sys
import unittest
import asyncio
from pathlib import Path

import httpx

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from common.store import get_store
from productRecommendationMicroservice.implementation.app import app
from recommendationEngineMicroservice.implementation.app import app as engine_app


def sample_payload() -> dict:
    return {
        "name": "Offer More Value",
        "description": "Upsell for an existing mobile customer",
        "instantSyncRecommendation": True,
        "recommendationType": "upsell",
        "category": [{"id": "mobile", "name": "Mobile"}],
        "channel": [{"id": "web", "name": "Web"}],
        "relatedParty": {"id": "cust-100", "role": "customer", "@referredType": "Individual"},
        "@type": "QueryProductRecommendation",
    }


class ProductRecommendationApiTest(unittest.TestCase):
    def setUp(self) -> None:
        get_store().reset()

    async def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    async def engine_request(self, method: str, path: str, **kwargs) -> httpx.Response:
        transport = httpx.ASGITransport(app=engine_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    def test_create_list_and_retrieve_recommendation(self) -> None:
        create_response = asyncio.run(
            self.request(
                "POST",
                "/tmf-api/recommendationManagement/v4/queryProductRecommendation",
                json=sample_payload(),
            )
        )
        self.assertEqual(create_response.status_code, 201, create_response.text)
        entity = create_response.json()
        self.assertEqual(entity["state"], "done")
        self.assertEqual(entity["recommendationType"], "upsell")
        self.assertGreaterEqual(len(entity["recommendationItem"]), 1)

        list_response = asyncio.run(self.request("GET", "/tmf-api/recommendationManagement/v4/queryProductRecommendation"))
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)

        retrieve_response = asyncio.run(
            self.request(
                "GET",
                f"/tmf-api/recommendationManagement/v4/queryProductRecommendation/{entity['id']}",
            )
        )
        self.assertEqual(retrieve_response.status_code, 200)
        self.assertEqual(retrieve_response.json()["id"], entity["id"])

    def test_invalid_payload_is_persisted_with_error_state(self) -> None:
        payload = sample_payload()
        payload["channel"] = "web"

        response = asyncio.run(
            self.request("POST", "/tmf-api/recommendationManagement/v4/queryProductRecommendation", json=payload)
        )
        self.assertEqual(response.status_code, 201, response.text)
        entity = response.json()
        self.assertEqual(entity["state"], "terminatedWithError")
        self.assertFalse(entity["validationResult"]["valid"])

    def test_patch_and_delete_are_not_supported_by_tmf680_resource(self) -> None:
        create_response = asyncio.run(
            self.request(
                "POST",
                "/tmf-api/recommendationManagement/v4/queryProductRecommendation",
                json=sample_payload(),
            )
        )
        entity = create_response.json()

        patch_response = asyncio.run(
            self.request(
                "PATCH",
                f"/tmf-api/recommendationManagement/v4/queryProductRecommendation/{entity['id']}",
                json={"state": "done"},
            )
        )
        self.assertEqual(patch_response.status_code, 405)

        delete_response = asyncio.run(
            self.request(
                "DELETE",
                f"/tmf-api/recommendationManagement/v4/queryProductRecommendation/{entity['id']}",
            )
        )
        self.assertEqual(delete_response.status_code, 405)

    def test_register_listener_is_idempotent(self) -> None:
        payload = {"callback": "http://listener.local/events", "query": "eventType=QueryProductRecommendationCreateEvent"}

        first = asyncio.run(self.request("POST", "/tmf-api/recommendationManagement/v4/hub", json=payload))
        second = asyncio.run(self.request("POST", "/tmf-api/recommendationManagement/v4/hub", json=payload))

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.json()["id"], second.json()["id"])

    def test_engine_returns_ranked_recommendations(self) -> None:
        response = asyncio.run(self.engine_request("POST", "/recommend/queryProductRecommendation", json=sample_payload()))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["validation"]["valid"])
        self.assertGreaterEqual(len(payload["recommendationItems"]), 1)
        self.assertEqual(payload["recommendationItems"][0]["priority"], 1)


if __name__ == "__main__":
    unittest.main()
