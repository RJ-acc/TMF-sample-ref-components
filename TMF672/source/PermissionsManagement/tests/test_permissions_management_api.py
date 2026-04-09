from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path

import httpx

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from common.access import resource_names
from common.store import get_store
from permissionsManagementEngineMicroservice.implementation.app import app as engine_app
from permissionsManagementMicroservice.implementation.app import LISTENER_OPERATIONS, app

API_BASE = "/tmf-api/rolesAndPermissions/v4"


def sample_payloads() -> dict[str, dict]:
    return {
        "permission": {
            "description": "Regional approval access for enterprise billing changes",
            "granter": {
                "id": "individual-9001",
                "name": "Avery Morgan",
                "role": "granter",
                "@referredType": "Individual",
            },
            "user": {
                "id": "individual-2001",
                "name": "Priya Raman",
                "role": "user",
                "@referredType": "Individual",
            },
            "validFor": {
                "startDateTime": "2026-04-01T00:00:00Z",
                "endDateTime": "2026-12-31T23:59:59Z",
            },
            "assetUserRole": [
                {
                    "manageableAsset": {
                        "id": "billing-account-2001",
                        "name": "Fabrikam Billing Account",
                        "@referredType": "BillingAccount",
                    },
                    "userRole": {
                        "id": "user-role-2001",
                        "href": f"{API_BASE}/userRole/user-role-2001",
                        "@referredType": "UserRole",
                    },
                }
            ],
            "privilege": [
                {
                    "action": "approve",
                    "function": "invoiceAdjustment",
                    "manageableAsset": {
                        "id": "billing-account-2001",
                        "name": "Fabrikam Billing Account",
                        "@referredType": "BillingAccount",
                    },
                }
            ],
            "@type": "Permission",
        },
        "userRole": {
            "involvementRole": "RegionalApprover",
            "entitlement": [
                {"action": "read", "function": "invoiceReview", "@type": "Entitlement"},
                {"action": "approve", "function": "invoiceAdjustment", "@type": "Entitlement"},
            ],
            "@type": "UserRole",
        },
    }


def field_selection(resource_name: str) -> str:
    return "id,description,@type" if resource_name == "permission" else "id,involvementRole,@type"


def patch_payload(resource_name: str) -> dict[str, str]:
    if resource_name == "permission":
        return {"description": "patched permission description", "state": "active"}
    return {"involvementRole": "RegionalApproverLead", "state": "active"}


class PermissionsManagementApiTest(unittest.TestCase):
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
        self.assertIn("listPermission", links)
        self.assertIn("createPermission", links)
        self.assertIn("retrievePermission", links)
        self.assertIn("patchPermission", links)
        self.assertIn("listUserRole", links)
        self.assertIn("createUserRole", links)
        self.assertIn("retrieveUserRole", links)
        self.assertIn("patchUserRole", links)
        self.assertNotIn("deletePermission", links)
        self.assertNotIn("deleteUserRole", links)
        for operation_name, _ in LISTENER_OPERATIONS:
            self.assertIn(operation_name, links)

    def test_each_resource_supports_list_create_retrieve_and_patch(self) -> None:
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

                patch_response = asyncio.run(
                    self.request(
                        "PATCH",
                        f"{API_BASE}/{resource_name}/{entity['id']}",
                        json=patch_payload(resource_name),
                    )
                )
                self.assertEqual(patch_response.status_code, 200, patch_response.text)
                if resource_name == "permission":
                    self.assertEqual(patch_response.json()["description"], "patched permission description")
                else:
                    self.assertEqual(patch_response.json()["involvementRole"], "RegionalApproverLead")

                updated_response = asyncio.run(self.request("GET", f"{API_BASE}/{resource_name}/{entity['id']}"))
                self.assertEqual(updated_response.status_code, 200)

    def test_list_filters_fields_and_pagination(self) -> None:
        response = asyncio.run(
            self.request(
                "GET",
                f"{API_BASE}/userRole",
                params={"fields": "id,involvementRole", "offset": 0, "limit": 1},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(sorted(response.json()[0].keys()), ["id", "involvementRole"])
        self.assertEqual(response.headers["X-Result-Count"], "1")

    def test_invalid_payloads_are_rejected(self) -> None:
        invalid_create = asyncio.run(
            self.request(
                "POST",
                f"{API_BASE}/permission",
                json={"description": "broken", "validFor": "not-an-object"},
            )
        )
        self.assertEqual(invalid_create.status_code, 400)
        self.assertFalse(invalid_create.json()["detail"]["valid"])

        invalid_patch = asyncio.run(
            self.request(
                "PATCH",
                f"{API_BASE}/userRole/user-role-1001",
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

                delete_item = asyncio.run(self.request("DELETE", f"{API_BASE}/{resource_name}/example-id"))
                self.assertEqual(delete_item.status_code, 405)

                post_item = asyncio.run(self.request("POST", f"{API_BASE}/{resource_name}/example-id", json={}))
                self.assertEqual(post_item.status_code, 405)

    def test_hub_idempotency_and_listener_routes(self) -> None:
        payload = {"callback": "http://listener.local/events", "query": "eventType=PermissionCreateEvent"}

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


if __name__ == "__main__":
    unittest.main()
