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

API_BASE = "/po1-productordercapturevalidation/tmf-api/productOrderingManagement/v4"


def sample_product_order() -> dict:
    return {
        "externalId": "order-100",
        "priority": "1",
        "notificationContact": "buyer@example.com",
        "relatedParty": [{"id": "cust-100", "role": "customer", "@referredType": "Individual"}],
        "productOrderItem": [
            {
                "id": "1",
                "action": "add",
                "quantity": 1,
                "productOffering": {"id": "offer-100", "name": "Starter Mobile Plan"},
            }
        ],
        "@type": "ProductOrder",
    }


class ProductOrderApiTest(unittest.TestCase):
    def setUp(self) -> None:
        get_store().reset()
        self.app = self._load_app()

    def _load_app(self):
        module_name = "productOrderCaptureValidationMicroservice.implementation.app"
        previous_api_base = os.environ.get("API_BASE_PATH")
        previous_component_name = os.environ.get("COMPONENT_NAME")
        previous_validation_url = os.environ.get("VALIDATION_SERVICE_URL")
        os.environ["API_BASE_PATH"] = API_BASE
        os.environ["COMPONENT_NAME"] = "po1-productordercapturevalidation"
        os.environ["VALIDATION_SERVICE_URL"] = "http://127.0.0.1:9999"
        try:
            sys.modules.pop(module_name, None)
            module = importlib.import_module(module_name)
            return module.app
        finally:
            if previous_api_base is None:
                os.environ.pop("API_BASE_PATH", None)
            else:
                os.environ["API_BASE_PATH"] = previous_api_base
            if previous_component_name is None:
                os.environ.pop("COMPONENT_NAME", None)
            else:
                os.environ["COMPONENT_NAME"] = previous_component_name
            if previous_validation_url is None:
                os.environ.pop("VALIDATION_SERVICE_URL", None)
            else:
                os.environ["VALIDATION_SERVICE_URL"] = previous_validation_url

    async def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    def test_product_order_crud_and_cancel_flow(self) -> None:
        create_response = asyncio.run(self.request("POST", f"{API_BASE}/productOrder", json=sample_product_order()))
        self.assertEqual(create_response.status_code, 201, create_response.text)
        order = create_response.json()
        self.assertEqual(order["state"], "acknowledged")

        list_response = asyncio.run(self.request("GET", f"{API_BASE}/productOrder"))
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)

        patch_response = asyncio.run(
            self.request("PATCH", f"{API_BASE}/productOrder/{order['id']}", json={"priority": "2"})
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.json()["priority"], "2")

        cancel_payload = {
            "cancellationReason": "Customer request",
            "productOrder": {"id": order["id"]},
            "@type": "CancelProductOrder",
        }
        cancel_response = asyncio.run(self.request("POST", f"{API_BASE}/cancelProductOrder", json=cancel_payload))
        self.assertEqual(cancel_response.status_code, 201, cancel_response.text)
        cancel_task = cancel_response.json()
        self.assertEqual(cancel_task["state"], "done")

        retrieve_response = asyncio.run(self.request("GET", f"{API_BASE}/productOrder/{order['id']}"))
        self.assertEqual(retrieve_response.status_code, 200)
        self.assertEqual(retrieve_response.json()["state"], "cancelled")

        cancel_list_response = asyncio.run(self.request("GET", f"{API_BASE}/cancelProductOrder"))
        self.assertEqual(cancel_list_response.status_code, 200)
        self.assertEqual(len(cancel_list_response.json()), 1)

        delete_response = asyncio.run(self.request("DELETE", f"{API_BASE}/productOrder/{order['id']}"))
        self.assertEqual(delete_response.status_code, 204)

    def test_product_order_accepts_nested_offering_names(self) -> None:
        payload = {
            "@type": "ProductOrder",
            "description": "Activate Spain Roaming Plan - Standard",
            "notificationContact": "govindrr@yahoo.com",
            "productOrderItem": [
                {
                    "@type": "ProductOrderItem",
                    "id": "1",
                    "action": "add",
                    "quantity": 1,
                    "productOffering": {
                        "@type": "ProductOfferingRef",
                        "id": "product-offering-0114c98c",
                        "name": "Spain Roaming Plan - Standard",
                    },
                    "product": {
                        "@type": "Product",
                        "name": "Spain Roaming Plan - Standard",
                    },
                }
            ],
            "relatedParty": [
                {
                    "@type": "RelatedParty",
                    "id": "C00000001",
                    "name": "Mary Jane",
                    "role": "Customer",
                    "contactMedium": [
                        {
                            "@type": "ContactMedium",
                            "mediumType": "email",
                            "characteristic": {"emailAddress": "govindrr@yahoo.com"},
                        }
                    ],
                }
            ],
            "requestedStartDate": "2026-04-14T00:00:00.000Z",
        }

        response = asyncio.run(self.request("POST", f"{API_BASE}/productOrder", json=payload))

        self.assertEqual(response.status_code, 201, response.text)
        entity = response.json()
        self.assertEqual(entity["state"], "acknowledged")
        self.assertTrue(entity["validationResult"]["valid"])
        item = entity["productOrderItem"][0]
        self.assertEqual(item["productOffering"]["name"], "Spain Roaming Plan - Standard")
        self.assertEqual(item["product"]["name"], "Spain Roaming Plan - Standard")

    def test_invalid_product_order_is_held(self) -> None:
        payload = sample_product_order()
        payload["productOrderItem"] = []

        response = asyncio.run(self.request("POST", f"{API_BASE}/productOrder", json=payload))
        self.assertEqual(response.status_code, 201, response.text)
        entity = response.json()
        self.assertEqual(entity["state"], "held")
        self.assertFalse(entity["validationResult"]["valid"])

    def test_hub_registration_is_idempotent(self) -> None:
        payload = {"callback": "http://listener.local/events", "query": "eventType=ProductOrderCreateEvent"}

        first = asyncio.run(self.request("POST", f"{API_BASE}/hub", json=payload))
        second = asyncio.run(self.request("POST", f"{API_BASE}/hub", json=payload))

        self.assertEqual(first.status_code, 201, first.text)
        self.assertEqual(second.status_code, 201, second.text)
        self.assertEqual(first.json()["id"], second.json()["id"])

        delete_response = asyncio.run(self.request("DELETE", f"{API_BASE}/hub/{first.json()['id']}"))
        self.assertEqual(delete_response.status_code, 204)


if __name__ == "__main__":
    unittest.main()
