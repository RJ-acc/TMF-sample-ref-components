from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path

import httpx

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from common.sla import resource_names
from common.store import get_store
from slaManagementEngineMicroservice.implementation.app import app as engine_app
from slaManagementMicroservice.implementation.app import LISTENER_OPERATIONS, app

API_BASE = "/tmf-api/slaManagement/v2"


def sample_payloads() -> dict[str, dict]:
    return {
        "sla": {
            "name": "Managed WAN Platinum SLA",
            "description": "High-availability SLA for managed WAN services.",
            "category": "managed-service",
            "state": "active",
            "validFor": {
                "startDateTime": "2026-04-01T00:00:00Z",
                "endDateTime": "2027-03-31T23:59:59Z",
            },
            "relatedEntity": [
                {"id": "service-2001", "name": "Managed WAN Platinum", "@referredType": "Service"}
            ],
            "serviceLevelObjective": [
                {
                    "id": "slo-3001",
                    "name": "Availability",
                    "description": "Monthly service availability target",
                    "targetEntity": "service-2001",
                    "targetValue": "99.99",
                    "unit": "percent",
                }
            ],
            "rule": [
                {
                    "name": "Availability threshold",
                    "metricName": "serviceAvailability",
                    "comparison": ">=",
                    "targetValue": "99.99",
                    "unit": "percent",
                }
            ],
            "@type": "SLA",
        },
        "slaViolation": {
            "name": "Managed WAN availability breach",
            "description": "Availability fell below contract during regional outage.",
            "state": "detected",
            "severity": "major",
            "reason": "Monthly availability measured at 99.70%.",
            "violationDate": "2026-04-09T08:15:00Z",
            "sla": {
                "id": "sla-1001",
                "href": f"{API_BASE}/sla/sla-1001",
                "name": "Enterprise Internet Gold SLA",
                "@referredType": "SLA",
            },
            "serviceLevelObjective": {
                "id": "slo-1001",
                "name": "Availability",
                "@referredType": "ServiceLevelObjective",
            },
            "relatedEntity": [
                {"id": "service-1001", "name": "Enterprise Internet Gold", "@referredType": "Service"}
            ],
            "@type": "SLAViolation",
        },
    }


def field_selection(resource_name: str) -> str:
    return "id,name,state,@type" if resource_name == "sla" else "id,name,severity,@type"


def replace_payload(resource_name: str) -> dict[str, object]:
    if resource_name == "sla":
        return {
            "name": "Managed WAN Platinum SLA Replacement",
            "description": "Replacement payload for SLA full update.",
            "category": "managed-service",
            "state": "suspended",
            "validFor": {
                "startDateTime": "2026-04-01T00:00:00Z",
                "endDateTime": "2027-03-31T23:59:59Z",
            },
            "relatedEntity": [
                {"id": "service-2001", "name": "Managed WAN Platinum", "@referredType": "Service"}
            ],
            "serviceLevelObjective": [
                {
                    "id": "slo-3001",
                    "name": "Availability",
                    "description": "Replacement objective",
                    "targetEntity": "service-2001",
                    "targetValue": "99.95",
                    "unit": "percent",
                }
            ],
            "@type": "SLA",
        }
    return {
        "name": "Managed WAN availability breach replacement",
        "description": "Replacement payload for SLA violation full update.",
        "state": "acknowledged",
        "severity": "critical",
        "reason": "Replacement violation reason.",
        "violationDate": "2026-04-09T09:00:00Z",
        "sla": {
            "id": "sla-1001",
            "href": f"{API_BASE}/sla/sla-1001",
            "name": "Enterprise Internet Gold SLA",
            "@referredType": "SLA",
        },
        "serviceLevelObjective": {
            "id": "slo-1001",
            "name": "Availability",
            "@referredType": "ServiceLevelObjective",
        },
        "@type": "SLAViolation",
    }


def patch_payload(resource_name: str) -> dict[str, str]:
    if resource_name == "sla":
        return {"description": "patched SLA description", "state": "retired"}
    return {"reason": "patched violation reason", "state": "resolved"}


class SLAManagementApiTest(unittest.TestCase):
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

    def test_api_directory_lists_supported_resources_and_listener_paths(self) -> None:
        response = asyncio.run(self.request("GET", API_BASE))
        self.assertEqual(response.status_code, 200)
        links = response.json()["_links"]

        self.assertIn("registerListener", links)
        self.assertIn("unregisterListener", links)
        self.assertIn("listSLA", links)
        self.assertIn("createSLA", links)
        self.assertIn("retrieveSLA", links)
        self.assertIn("deleteSLA", links)
        self.assertIn("replaceSLA", links)
        self.assertIn("patchSLA", links)
        self.assertIn("listSLAViolation", links)
        self.assertIn("createSLAViolation", links)
        self.assertIn("retrieveSLAViolation", links)
        self.assertIn("deleteSLAViolation", links)
        self.assertIn("replaceSLAViolation", links)
        self.assertIn("patchSLAViolation", links)
        self.assertIn("listHub", links)
        self.assertIn("retrieveListener", links)
        for operation_name, _ in LISTENER_OPERATIONS:
            self.assertIn(operation_name, links)

    def test_each_resource_supports_list_create_retrieve_replace_patch_and_delete(self) -> None:
        for resource_name, payload in sample_payloads().items():
            with self.subTest(resource=resource_name):
                list_response = asyncio.run(self.request("GET", f"{API_BASE}/{resource_name}"))
                self.assertEqual(list_response.status_code, 200)
                self.assertGreaterEqual(len(list_response.json()), 2)

                create_response = asyncio.run(self.request("POST", f"{API_BASE}/{resource_name}", json=payload))
                self.assertEqual(create_response.status_code, 201, create_response.text)
                entity = create_response.json()
                self.assertEqual(entity["@type"], payload["@type"])
                self.assertTrue(entity["href"].endswith(f"/{resource_name}/{entity['id']}"))

                retrieve_response = asyncio.run(
                    self.request(
                        "GET",
                        f"{API_BASE}/{resource_name}/{entity['id']}",
                        params={"fields": field_selection(resource_name)},
                    )
                )
                self.assertEqual(retrieve_response.status_code, 200)
                self.assertEqual(retrieve_response.json()["id"], entity["id"])

                replace_response = asyncio.run(
                    self.request(
                        "PUT",
                        f"{API_BASE}/{resource_name}/{entity['id']}",
                        json=replace_payload(resource_name),
                    )
                )
                self.assertEqual(replace_response.status_code, 200, replace_response.text)
                self.assertEqual(replace_response.json()["id"], entity["id"])

                patch_response = asyncio.run(
                    self.request(
                        "PATCH",
                        f"{API_BASE}/{resource_name}/{entity['id']}",
                        json=patch_payload(resource_name),
                    )
                )
                self.assertEqual(patch_response.status_code, 200, patch_response.text)
                if resource_name == "sla":
                    self.assertEqual(patch_response.json()["description"], "patched SLA description")
                else:
                    self.assertEqual(patch_response.json()["reason"], "patched violation reason")

                delete_response = asyncio.run(self.request("DELETE", f"{API_BASE}/{resource_name}/{entity['id']}"))
                self.assertEqual(delete_response.status_code, 204)

                updated_response = asyncio.run(self.request("GET", f"{API_BASE}/{resource_name}/{entity['id']}"))
                self.assertEqual(updated_response.status_code, 404)

    def test_list_filters_fields_and_pagination(self) -> None:
        response = asyncio.run(
            self.request(
                "GET",
                f"{API_BASE}/sla",
                params={"fields": "id,name,state", "offset": 0, "limit": 1},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(sorted(response.json()[0].keys()), ["id", "name", "state"])
        self.assertEqual(response.headers["X-Result-Count"], "1")

    def test_invalid_payloads_are_rejected(self) -> None:
        invalid_create = asyncio.run(
            self.request(
                "POST",
                f"{API_BASE}/sla",
                json={"name": "broken", "validFor": "not-an-object"},
            )
        )
        self.assertEqual(invalid_create.status_code, 400)
        self.assertFalse(invalid_create.json()["detail"]["valid"])

        invalid_patch = asyncio.run(
            self.request(
                "PATCH",
                f"{API_BASE}/slaViolation/sla-violation-1001",
                json={"id": "forbidden"},
            )
        )
        self.assertEqual(invalid_patch.status_code, 400)
        self.assertFalse(invalid_patch.json()["detail"]["valid"])

        invalid_replace = asyncio.run(
            self.request(
                "PUT",
                f"{API_BASE}/sla/sla-1001",
                json={"description": "missing required fields"},
            )
        )
        self.assertEqual(invalid_replace.status_code, 400)
        self.assertFalse(invalid_replace.json()["detail"]["valid"])

    def test_unsupported_method_combinations_return_405(self) -> None:
        for resource_name in resource_names():
            with self.subTest(resource=resource_name):
                patch_collection = asyncio.run(self.request("PATCH", f"{API_BASE}/{resource_name}", json={}))
                self.assertEqual(patch_collection.status_code, 405)

                put_collection = asyncio.run(self.request("PUT", f"{API_BASE}/{resource_name}", json={}))
                self.assertEqual(put_collection.status_code, 405)

                delete_collection = asyncio.run(self.request("DELETE", f"{API_BASE}/{resource_name}"))
                self.assertEqual(delete_collection.status_code, 405)

                post_item = asyncio.run(self.request("POST", f"{API_BASE}/{resource_name}/example-id", json={}))
                self.assertEqual(post_item.status_code, 405)

    def test_hub_idempotency_and_listener_routes(self) -> None:
        payload = {"callback": "http://listener.local/events", "query": "eventType=SLACreateEvent"}

        first = asyncio.run(self.request("POST", f"{API_BASE}/hub", json=payload))
        second = asyncio.run(self.request("POST", f"{API_BASE}/hub", json=payload))
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.json()["id"], second.json()["id"])

        list_response = asyncio.run(self.request("GET", f"{API_BASE}/hub"))
        self.assertEqual(list_response.status_code, 200)
        self.assertGreaterEqual(len(list_response.json()), 1)

        retrieve_response = asyncio.run(self.request("GET", f"{API_BASE}/hub/{first.json()['id']}"))
        self.assertEqual(retrieve_response.status_code, 200)
        self.assertEqual(retrieve_response.json()["id"], first.json()["id"])

        for _, listener_path in LISTENER_OPERATIONS:
            response = asyncio.run(self.request("POST", f"{API_BASE}{listener_path}", json={"eventType": "sample"}))
            self.assertEqual(response.status_code, 204, listener_path)

        delete_response = asyncio.run(self.request("DELETE", f"{API_BASE}/hub/{first.json()['id']}"))
        self.assertEqual(delete_response.status_code, 204)

    def test_engine_routes_cover_seeded_resources_and_validation(self) -> None:
        for resource_name, payload in sample_payloads().items():
            with self.subTest(resource=resource_name):
                list_response = asyncio.run(self.engine_request("GET", f"/{resource_name}"))
                self.assertEqual(list_response.status_code, 200)
                self.assertGreaterEqual(list_response.json()["count"], 2)

                validate_create = asyncio.run(self.engine_request("POST", f"/validate/{resource_name}", json=payload))
                self.assertEqual(validate_create.status_code, 200)
                self.assertTrue(validate_create.json()["valid"])

                validate_patch = asyncio.run(
                    self.engine_request("POST", f"/validate/{resource_name}/patch", json=patch_payload(resource_name))
                )
                self.assertEqual(validate_patch.status_code, 200)
                self.assertTrue(validate_patch.json()["valid"])

                validate_replace = asyncio.run(
                    self.engine_request("POST", f"/validate/{resource_name}/replace", json=replace_payload(resource_name))
                )
                self.assertEqual(validate_replace.status_code, 200)
                self.assertTrue(validate_replace.json()["valid"])


if __name__ == "__main__":
    unittest.main()
