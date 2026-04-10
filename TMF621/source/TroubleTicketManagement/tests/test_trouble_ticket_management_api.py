from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path

import httpx

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from common.store import get_store
from common.tickets import resource_names
from troubleTicketManagementEngineMicroservice.implementation.app import app as engine_app
from troubleTicketManagementMicroservice.implementation.app import LISTENER_OPERATIONS, app

API_BASE = "/tmf-api/troubleTicket/v5"


def sample_ticket_payload() -> dict[str, object]:
    return {
        "@type": "TroubleTicket",
        "name": "Intermittent mobile data failure",
        "description": "Customer reported repeated mobile data session drops while commuting.",
        "severity": "major",
        "priority": "high",
        "ticketType": "incident",
        "status": "acknowledged",
        "relatedParty": [
            {
                "@type": "RelatedParty",
                "role": "originator",
                "partyOrPartyRole": {"@type": "PartyRef", "id": "party-1003", "name": "Priya Raman"},
            }
        ],
        "relatedEntity": [
            {
                "@type": "EntityRef",
                "role": "service",
                "entity": {"@type": "EntityRef", "id": "svc-1003", "name": "5G Unlimited"},
            }
        ],
        "note": [
            {
                "@type": "Note",
                "author": "Agent Noor",
                "text": "Opened engineering investigation after collecting device diagnostics.",
            }
        ],
    }


def sample_spec_payload() -> dict[str, object]:
    return {
        "@type": "TroubleTicketSpecification",
        "name": "Mobile service degradation ticket",
        "description": "Template used for mobile service instability and packet-loss reports.",
        "version": "2.1",
        "lifecycleStatus": "active",
        "relatedEntity": [
            {
                "@type": "EntityRef",
                "role": "productSpecification",
                "entity": {"@type": "EntityRef", "id": "ps-2201", "name": "5G Unlimited"},
            }
        ],
    }


class TroubleTicketManagementApiTest(unittest.TestCase):
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
        self.assertIn("retrieveListener", links)
        self.assertIn("unregisterListener", links)
        self.assertIn("listTroubleTicket", links)
        self.assertIn("createTroubleTicket", links)
        self.assertIn("retrieveTroubleTicket", links)
        self.assertIn("patchTroubleTicket", links)
        self.assertIn("deleteTroubleTicket", links)
        self.assertIn("listTroubleTicketSpecification", links)
        self.assertIn("createTroubleTicketSpecification", links)
        for operation_name, _ in LISTENER_OPERATIONS:
            self.assertIn(operation_name, links)

    def test_trouble_ticket_and_specification_support_full_crud(self) -> None:
        list_response = asyncio.run(self.request("GET", f"{API_BASE}/troubleTicket"))
        self.assertEqual(list_response.status_code, 200)
        self.assertGreaterEqual(len(list_response.json()), 2)

        create_ticket = asyncio.run(self.request("POST", f"{API_BASE}/troubleTicket", json=sample_ticket_payload()))
        self.assertEqual(create_ticket.status_code, 201, create_ticket.text)
        ticket = create_ticket.json()
        self.assertEqual(ticket["@type"], "TroubleTicket")
        self.assertTrue(ticket["href"].endswith(f"/troubleTicket/{ticket['id']}"))

        create_spec = asyncio.run(
            self.request("POST", f"{API_BASE}/troubleTicketSpecification", json=sample_spec_payload())
        )
        self.assertEqual(create_spec.status_code, 201, create_spec.text)
        specification = create_spec.json()
        self.assertEqual(specification["@type"], "TroubleTicketSpecification")
        self.assertTrue(specification["href"].endswith(f"/troubleTicketSpecification/{specification['id']}"))

        retrieve_response = asyncio.run(
            self.request("GET", f"{API_BASE}/troubleTicket/{ticket['id']}", params={"fields": "id,severity,status"})
        )
        self.assertEqual(retrieve_response.status_code, 200)
        self.assertEqual(retrieve_response.json()["id"], ticket["id"])

        patch_ticket = asyncio.run(
            self.request(
                "PATCH",
                f"{API_BASE}/troubleTicket/{ticket['id']}",
                json={"description": "patched trouble ticket", "status": "resolved"},
            )
        )
        self.assertEqual(patch_ticket.status_code, 200, patch_ticket.text)
        self.assertEqual(patch_ticket.json()["status"], "resolved")
        self.assertIn("resolutionDate", patch_ticket.json())

        patch_spec = asyncio.run(
            self.request(
                "PATCH",
                f"{API_BASE}/troubleTicketSpecification/{specification['id']}",
                json={"lifecycleStatus": "retired"},
            )
        )
        self.assertEqual(patch_spec.status_code, 200, patch_spec.text)
        self.assertEqual(patch_spec.json()["lifecycleStatus"], "retired")

        delete_ticket = asyncio.run(self.request("DELETE", f"{API_BASE}/troubleTicket/{ticket['id']}"))
        self.assertEqual(delete_ticket.status_code, 204)

        delete_spec = asyncio.run(self.request("DELETE", f"{API_BASE}/troubleTicketSpecification/{specification['id']}"))
        self.assertEqual(delete_spec.status_code, 204)

        missing_response = asyncio.run(self.request("GET", f"{API_BASE}/troubleTicket/{ticket['id']}"))
        self.assertEqual(missing_response.status_code, 404)

    def test_list_filters_fields_and_pagination(self) -> None:
        response = asyncio.run(
            self.request(
                "GET",
                f"{API_BASE}/troubleTicket",
                params={"fields": "id,severity,status", "offset": 0, "limit": 1},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(sorted(response.json()[0].keys()), ["id", "severity", "status"])
        self.assertEqual(response.headers["X-Result-Count"], "1")

    def test_invalid_payloads_are_rejected(self) -> None:
        invalid_create = asyncio.run(
            self.request(
                "POST",
                f"{API_BASE}/troubleTicket",
                json={"@type": "TroubleTicket", "description": "broken", "relatedParty": "nope"},
            )
        )
        self.assertEqual(invalid_create.status_code, 400)
        self.assertFalse(invalid_create.json()["detail"]["valid"])

        invalid_patch = asyncio.run(
            self.request(
                "PATCH",
                f"{API_BASE}/troubleTicketSpecification/tts-1001",
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

    def test_hub_idempotency_retrieve_and_listener_routes(self) -> None:
        payload = {"callback": "http://listener.local/events", "query": "eventType=TroubleTicketCreateEvent"}

        first = asyncio.run(self.request("POST", f"{API_BASE}/hub", json=payload))
        second = asyncio.run(self.request("POST", f"{API_BASE}/hub", json=payload))
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.json()["id"], second.json()["id"])

        retrieve = asyncio.run(self.request("GET", f"{API_BASE}/hub/{first.json()['id']}"))
        self.assertEqual(retrieve.status_code, 200)
        self.assertEqual(retrieve.json()["id"], first.json()["id"])

        for _, listener_path in LISTENER_OPERATIONS:
            response = asyncio.run(self.request("POST", f"{API_BASE}{listener_path}", json={"eventType": "sample"}))
            self.assertEqual(response.status_code, 204, listener_path)

        delete_response = asyncio.run(self.request("DELETE", f"{API_BASE}/hub/{first.json()['id']}"))
        self.assertEqual(delete_response.status_code, 204)

    def test_engine_routes_cover_seeded_resources_and_validation(self) -> None:
        payloads = {
            "troubleTicket": sample_ticket_payload(),
            "troubleTicketSpecification": sample_spec_payload(),
        }
        patches = {
            "troubleTicket": {"description": "patched ticket", "status": "pending"},
            "troubleTicketSpecification": {"lifecycleStatus": "retired"},
        }
        for resource_name in resource_names():
            with self.subTest(resource=resource_name):
                list_response = asyncio.run(self.engine_request("GET", f"/{resource_name}"))
                self.assertEqual(list_response.status_code, 200)
                self.assertGreaterEqual(list_response.json()["count"], 2)

                validate_create = asyncio.run(
                    self.engine_request("POST", f"/validate/{resource_name}", json=payloads[resource_name])
                )
                self.assertEqual(validate_create.status_code, 200)
                self.assertTrue(validate_create.json()["valid"])

                validate_patch = asyncio.run(
                    self.engine_request(
                        "POST",
                        f"/validate/{resource_name}/patch",
                        json=patches[resource_name],
                    )
                )
                self.assertEqual(validate_patch.status_code, 200)
                self.assertTrue(validate_patch.json()["valid"])


if __name__ == "__main__":
    unittest.main()
