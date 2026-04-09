from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path

import httpx

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from common.interactions import resource_names
from common.store import get_store
from partyInteractionManagementEngineMicroservice.implementation.app import app as engine_app
from partyInteractionManagementMicroservice.implementation.app import LISTENER_OPERATIONS, app

API_BASE = "/tmf-api/partyInteractionManagement/v5"


def sample_payload() -> dict[str, object]:
    return {
        "@type": "PartyInteraction",
        "direction": "inbound",
        "reason": "Customer requested billing clarification",
        "interactionDate": {
            "startDateTime": "2026-04-09T10:00:00Z",
            "endDateTime": "2026-04-09T10:15:00Z",
        },
        "description": "Customer used the mobile app chat to ask about a recent invoice adjustment.",
        "status": "opened",
        "relatedChannel": [
            {
                "@type": "RelatedChannel",
                "role": "contactChannel",
                "channel": {
                    "@type": "ChannelRef",
                    "id": "mobile-app",
                    "name": "Mobile App",
                    "@referredType": "Channel",
                },
            }
        ],
        "relatedParty": [
            {
                "@type": "RelatedPartyOrPartyRole",
                "role": "customer",
                "partyOrPartyRole": {
                    "@type": "PartyRef",
                    "id": "party-1003",
                    "name": "Priya Raman",
                    "@referredType": "Individual",
                },
            }
        ],
        "note": [
            {
                "@type": "Note",
                "author": "Agent Noor",
                "text": "Explained the tax component and opened follow-up task for finance.",
            }
        ],
    }


class PartyInteractionManagementApiTest(unittest.TestCase):
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

    def test_api_directory_lists_crud_resources_and_listener_paths(self) -> None:
        response = asyncio.run(self.request("GET", API_BASE))
        self.assertEqual(response.status_code, 200)
        links = response.json()["_links"]

        self.assertIn("registerListener", links)
        self.assertIn("unregisterListener", links)
        self.assertIn("listPartyInteraction", links)
        self.assertIn("createPartyInteraction", links)
        self.assertIn("retrievePartyInteraction", links)
        self.assertIn("patchPartyInteraction", links)
        self.assertIn("deletePartyInteraction", links)
        for operation_name, _ in LISTENER_OPERATIONS:
            self.assertIn(operation_name, links)

    def test_party_interaction_supports_full_crud(self) -> None:
        list_response = asyncio.run(self.request("GET", f"{API_BASE}/partyInteraction"))
        self.assertEqual(list_response.status_code, 200)
        self.assertGreaterEqual(len(list_response.json()), 2)

        create_response = asyncio.run(self.request("POST", f"{API_BASE}/partyInteraction", json=sample_payload()))
        self.assertEqual(create_response.status_code, 201, create_response.text)
        entity = create_response.json()
        self.assertEqual(entity["@type"], "PartyInteraction")
        self.assertTrue(entity["href"].endswith(f"/partyInteraction/{entity['id']}"))

        retrieve_response = asyncio.run(
            self.request("GET", f"{API_BASE}/partyInteraction/{entity['id']}", params={"fields": "id,reason,status"})
        )
        self.assertEqual(retrieve_response.status_code, 200)
        self.assertEqual(retrieve_response.json()["id"], entity["id"])

        patch_response = asyncio.run(
            self.request(
                "PATCH",
                f"{API_BASE}/partyInteraction/{entity['id']}",
                json={"description": "patched interaction", "status": "completed"},
            )
        )
        self.assertEqual(patch_response.status_code, 200, patch_response.text)
        self.assertEqual(patch_response.json()["status"], "completed")

        delete_response = asyncio.run(self.request("DELETE", f"{API_BASE}/partyInteraction/{entity['id']}"))
        self.assertEqual(delete_response.status_code, 204)

        missing_response = asyncio.run(self.request("GET", f"{API_BASE}/partyInteraction/{entity['id']}"))
        self.assertEqual(missing_response.status_code, 404)

    def test_list_filters_fields_and_pagination(self) -> None:
        response = asyncio.run(
            self.request(
                "GET",
                f"{API_BASE}/partyInteraction",
                params={"fields": "id,reason,status", "offset": 0, "limit": 1},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(sorted(response.json()[0].keys()), ["id", "reason", "status"])
        self.assertEqual(response.headers["X-Result-Count"], "1")

    def test_invalid_payloads_are_rejected(self) -> None:
        invalid_create = asyncio.run(
            self.request(
                "POST",
                f"{API_BASE}/partyInteraction",
                json={"@type": "PartyInteraction", "direction": "inbound", "reason": "broken", "relatedChannel": "nope"},
            )
        )
        self.assertEqual(invalid_create.status_code, 400)
        self.assertFalse(invalid_create.json()["detail"]["valid"])

        invalid_patch = asyncio.run(
            self.request(
                "PATCH",
                f"{API_BASE}/partyInteraction/party-interaction-1001",
                json={"id": "forbidden"},
            )
        )
        self.assertEqual(invalid_patch.status_code, 400)
        self.assertFalse(invalid_patch.json()["detail"]["valid"])

    def test_unsupported_method_combinations_return_405(self) -> None:
        for resource_name in resource_names():
            with self.subTest(resource=resource_name):
                patch_collection = asyncio.run(self.request("PATCH", f"{API_BASE}/{resource_name}", json={}))
                self.assertEqual(patch_collection.status_code, 405)

                delete_collection = asyncio.run(self.request("DELETE", f"{API_BASE}/{resource_name}"))
                self.assertEqual(delete_collection.status_code, 405)

                post_item = asyncio.run(self.request("POST", f"{API_BASE}/{resource_name}/example-id", json={}))
                self.assertEqual(post_item.status_code, 405)

    def test_hub_idempotency_and_listener_routes(self) -> None:
        payload = {"callback": "http://listener.local/events", "query": "eventType=PartyInteractionCreateEvent"}

        first = asyncio.run(self.request("POST", f"{API_BASE}/hub", json=payload))
        second = asyncio.run(self.request("POST", f"{API_BASE}/hub", json=payload))
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.json()["id"], second.json()["id"])

        for _, listener_path in LISTENER_OPERATIONS:
            response = asyncio.run(self.request("POST", f"{API_BASE}{listener_path}", json={"eventType": "sample"}))
            self.assertEqual(response.status_code, 204, listener_path)

        delete_response = asyncio.run(self.request("DELETE", f"{API_BASE}/hub/{first.json()['id']}"))
        self.assertEqual(delete_response.status_code, 204)

    def test_engine_routes_cover_seeded_resources_and_validation(self) -> None:
        for resource_name in resource_names():
            with self.subTest(resource=resource_name):
                list_response = asyncio.run(self.engine_request("GET", f"/{resource_name}"))
                self.assertEqual(list_response.status_code, 200)
                self.assertGreaterEqual(list_response.json()["count"], 2)

                validate_create = asyncio.run(
                    self.engine_request("POST", f"/validate/{resource_name}", json=sample_payload())
                )
                self.assertEqual(validate_create.status_code, 200)
                self.assertTrue(validate_create.json()["valid"])

                validate_patch = asyncio.run(
                    self.engine_request(
                        "POST",
                        f"/validate/{resource_name}/patch",
                        json={"description": "patched interaction", "status": "completed"},
                    )
                )
                self.assertEqual(validate_patch.status_code, 200)
                self.assertTrue(validate_patch.json()["valid"])


if __name__ == "__main__":
    unittest.main()
