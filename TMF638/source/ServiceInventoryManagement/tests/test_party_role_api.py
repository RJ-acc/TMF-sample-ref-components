from __future__ import annotations

import asyncio
import importlib
import os
import sys
import unittest
from pathlib import Path

import httpx

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from common.store import get_store

API_BASE = "/pi1-serviceinventorymanagement/tmf-api/partyRoleManagement/v4"
LISTENER_PATHS = [
    f"{API_BASE}/listener/partyRoleAttributeValueChangeEvent",
    f"{API_BASE}/listener/partyRoleCreateEvent",
    f"{API_BASE}/listener/partyRoleDeleteEvent",
    f"{API_BASE}/listener/partyRoleStateChangeEvent",
]


class PartyRoleApiTest(unittest.TestCase):
    def setUp(self) -> None:
        get_store().reset()
        self.app = self._load_app()

    def _load_app(self):
        module_name = "partyRoleMicroservice.implementation.app"
        previous = os.environ.get("API_BASE_PATH")
        os.environ["API_BASE_PATH"] = API_BASE
        try:
            sys.modules.pop(module_name, None)
            module = importlib.import_module(module_name)
            return module.app
        finally:
            if previous is None:
                os.environ.pop("API_BASE_PATH", None)
            else:
                os.environ["API_BASE_PATH"] = previous

    async def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    def test_crud_operations_work(self) -> None:
        create_response = asyncio.run(
            self.request("POST", f"{API_BASE}/partyRole", json={"name": "Admin", "role": "admin"})
        )
        self.assertEqual(create_response.status_code, 201, create_response.text)
        entity = create_response.json()

        list_response = asyncio.run(self.request("GET", f"{API_BASE}/partyRole"))
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)

        patch_response = asyncio.run(
            self.request("PATCH", f"{API_BASE}/partyRole/{entity['id']}", json={"state": "inactive"})
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.json()["state"], "inactive")

        delete_response = asyncio.run(self.request("DELETE", f"{API_BASE}/partyRole/{entity['id']}"))
        self.assertEqual(delete_response.status_code, 204)

    def test_hub_registration_and_listener_examples_work(self) -> None:
        payload = {"callback": "http://listener.local/events", "query": "eventType=PartyRoleCreateEvent"}

        first = asyncio.run(self.request("POST", f"{API_BASE}/hub", json=payload))
        second = asyncio.run(self.request("POST", f"{API_BASE}/hub", json=payload))

        self.assertEqual(first.status_code, 201, first.text)
        self.assertEqual(second.status_code, 201, second.text)
        self.assertEqual(first.json()["id"], second.json()["id"])

        for path in LISTENER_PATHS:
            response = asyncio.run(self.request("POST", path, json={"eventType": "sample"}))
            self.assertEqual(response.status_code, 204, path)

        delete_response = asyncio.run(self.request("DELETE", f"{API_BASE}/hub/{first.json()['id']}"))
        self.assertEqual(delete_response.status_code, 204)


if __name__ == "__main__":
    unittest.main()
