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
from configurationEngineMicroservice.implementation.app import app as engine_app
from productConfigurationMicroservice.implementation.app import app


def sample_query_payload() -> dict:
    return {
        "name": "Configure handset",
        "instantSync": True,
        "channel": {"id": "web", "name": "Web", "@type": "ChannelRef"},
        "relatedParty": [{"id": "cust-100", "role": "customer", "@referredType": "Individual"}],
        "contextEntity": {"id": "quote-77", "name": "Quote 77", "@type": "EntityRef"},
        "requestProductConfigurationItem": [
            {
                "id": "01",
                "@type": "QueryProductConfigurationItem",
                "productConfiguration": {
                    "@type": "ProductConfiguration",
                    "productOffering": {"id": "14305", "name": "Mobile Handset", "@type": "ProductOfferingRef"},
                    "configurationAction": [
                        {"@type": "ConfigurationAction", "action": "add", "isSelected": True}
                    ],
                },
            }
        ],
        "@type": "QueryProductConfiguration",
    }


def sample_check_payload(*, missing_required_value: bool = False) -> dict:
    color_value = []
    if not missing_required_value:
        color_value = [
            {
                "@type": "ConfigurationCharacteristicValue",
                "isSelected": True,
                "isVisible": True,
                "characteristicValue": {
                    "name": "Color",
                    "value": "Blue",
                    "@type": "StringCharacteristic",
                },
            }
        ]
    storage_value = [
        {
            "@type": "ConfigurationCharacteristicValue",
            "isSelected": True,
            "isVisible": True,
            "characteristicValue": {
                "name": "Storage",
                "value": "128GB",
                "@type": "StringCharacteristic",
            },
        }
    ]

    return {
        "name": "Check handset configuration",
        "instantSync": True,
        "provideAlternatives": True,
        "channel": {"id": "web", "name": "Web", "@type": "ChannelRef"},
        "relatedParty": [{"id": "cust-100", "role": "customer", "@referredType": "Individual"}],
        "checkProductConfigurationItem": [
            {
                "id": "01",
                "@type": "CheckProductConfigurationItem",
                "productConfiguration": {
                    "@type": "ProductConfiguration",
                    "productOffering": {"id": "14305", "name": "Mobile Handset", "@type": "ProductOfferingRef"},
                    "configurationAction": [
                        {"@type": "ConfigurationAction", "action": "add", "isSelected": True}
                    ],
                    "configurationCharacteristic": [
                        {
                            "@type": "ConfigurationCharacteristic",
                            "id": "77",
                            "name": "Color",
                            "configurationCharacteristicValue": color_value,
                        },
                        {
                            "@type": "ConfigurationCharacteristic",
                            "id": "78",
                            "name": "Storage",
                            "configurationCharacteristicValue": storage_value,
                        }
                    ],
                },
            }
        ],
        "@type": "CheckProductConfiguration",
    }


class ProductConfiguratorApiTest(unittest.TestCase):
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

    def test_query_create_list_retrieve_and_fields(self) -> None:
        create_response = asyncio.run(
            self.request(
                "POST",
                "/tmf-api/productConfiguration/v5/queryProductConfiguration",
                json=sample_query_payload(),
            )
        )
        self.assertEqual(create_response.status_code, 200, create_response.text)
        entity = create_response.json()
        self.assertEqual(entity["state"], "done")
        self.assertGreaterEqual(len(entity["computedProductConfigurationItem"]), 1)

        list_response = asyncio.run(self.request("GET", "/tmf-api/productConfiguration/v5/queryProductConfiguration"))
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)
        self.assertEqual(list_response.headers["X-Total-Count"], "1")
        self.assertEqual(list_response.headers["X-Result-Count"], "1")

        retrieve_response = asyncio.run(
            self.request(
                "GET",
                f"/tmf-api/productConfiguration/v5/queryProductConfiguration/{entity['id']}",
                params={"fields": "id,state"},
            )
        )
        self.assertEqual(retrieve_response.status_code, 200)
        self.assertEqual(retrieve_response.json(), {"id": entity["id"], "state": "done"})

    def test_check_create_list_and_retrieve_rejected_configuration(self) -> None:
        create_response = asyncio.run(
            self.request(
                "POST",
                "/tmf-api/productConfiguration/v5/checkProductConfiguration",
                json=sample_check_payload(missing_required_value=True),
            )
        )
        self.assertEqual(create_response.status_code, 200, create_response.text)
        entity = create_response.json()
        self.assertEqual(entity["state"], "done")
        self.assertEqual(entity["checkProductConfigurationItem"][0]["state"], "rejected")
        self.assertIn("alternateProductConfigurationProposal", entity["checkProductConfigurationItem"][0])

        list_response = asyncio.run(self.request("GET", "/tmf-api/productConfiguration/v5/checkProductConfiguration"))
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)

        retrieve_response = asyncio.run(
            self.request(
                "GET",
                f"/tmf-api/productConfiguration/v5/checkProductConfiguration/{entity['id']}",
            )
        )
        self.assertEqual(retrieve_response.status_code, 200)
        self.assertEqual(retrieve_response.json()["id"], entity["id"])

    def test_invalid_payload_is_persisted_with_error_state(self) -> None:
        payload = sample_query_payload()
        payload["requestProductConfigurationItem"] = "broken"

        response = asyncio.run(
            self.request("POST", "/tmf-api/productConfiguration/v5/queryProductConfiguration", json=payload)
        )
        self.assertEqual(response.status_code, 200, response.text)
        entity = response.json()
        self.assertEqual(entity["state"], "terminatedWithError")
        self.assertFalse(entity["validationResult"]["valid"])

    def test_patch_and_delete_are_not_supported_by_tmf760_resources(self) -> None:
        query_response = asyncio.run(
            self.request("POST", "/tmf-api/productConfiguration/v5/queryProductConfiguration", json=sample_query_payload())
        )
        check_response = asyncio.run(
            self.request("POST", "/tmf-api/productConfiguration/v5/checkProductConfiguration", json=sample_check_payload())
        )
        query_id = query_response.json()["id"]
        check_id = check_response.json()["id"]

        query_patch = asyncio.run(
            self.request(
                "PATCH",
                f"/tmf-api/productConfiguration/v5/queryProductConfiguration/{query_id}",
                json={"state": "done"},
            )
        )
        self.assertEqual(query_patch.status_code, 405)

        query_delete = asyncio.run(
            self.request(
                "DELETE",
                f"/tmf-api/productConfiguration/v5/queryProductConfiguration/{query_id}",
            )
        )
        self.assertEqual(query_delete.status_code, 405)

        check_patch = asyncio.run(
            self.request(
                "PATCH",
                f"/tmf-api/productConfiguration/v5/checkProductConfiguration/{check_id}",
                json={"state": "done"},
            )
        )
        self.assertEqual(check_patch.status_code, 405)

        check_delete = asyncio.run(
            self.request(
                "DELETE",
                f"/tmf-api/productConfiguration/v5/checkProductConfiguration/{check_id}",
            )
        )
        self.assertEqual(check_delete.status_code, 405)

    def test_register_listener_is_idempotent_and_unregistration_works(self) -> None:
        payload = {"callback": "http://listener.local/events", "query": "eventType=QueryProductConfigurationCreateEvent"}

        first = asyncio.run(self.request("POST", "/tmf-api/productConfiguration/v5/hub", json=payload))
        second = asyncio.run(self.request("POST", "/tmf-api/productConfiguration/v5/hub", json=payload))

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.json()["id"], second.json()["id"])

        delete_response = asyncio.run(
            self.request("DELETE", f"/tmf-api/productConfiguration/v5/hub/{first.json()['id']}")
        )
        self.assertEqual(delete_response.status_code, 204)

    def test_all_listener_endpoints_acknowledge(self) -> None:
        listener_paths = [
            "/tmf-api/productConfiguration/v5/listener/checkProductConfigurationAttributeValueChangeEvent",
            "/tmf-api/productConfiguration/v5/listener/checkProductConfigurationCreateEvent",
            "/tmf-api/productConfiguration/v5/listener/checkProductConfigurationDeleteEvent",
            "/tmf-api/productConfiguration/v5/listener/checkProductConfigurationStateChangeEvent",
            "/tmf-api/productConfiguration/v5/listener/queryProductConfigurationAttributeValueChangeEvent",
            "/tmf-api/productConfiguration/v5/listener/queryProductConfigurationCreateEvent",
            "/tmf-api/productConfiguration/v5/listener/queryProductConfigurationDeleteEvent",
            "/tmf-api/productConfiguration/v5/listener/queryProductConfigurationStateChangeEvent",
        ]
        for path in listener_paths:
            response = asyncio.run(self.request("POST", path, json={"eventType": "noop"}))
            self.assertEqual(response.status_code, 204, path)

    def test_engine_query_and_check(self) -> None:
        query_response = asyncio.run(
            self.engine_request("POST", "/configure/queryProductConfiguration", json=sample_query_payload())
        )
        self.assertEqual(query_response.status_code, 200)
        query_payload = query_response.json()
        self.assertTrue(query_payload["validation"]["valid"])
        self.assertGreaterEqual(len(query_payload["computedItems"]), 1)

        check_response = asyncio.run(
            self.engine_request("POST", "/check/checkProductConfiguration", json=sample_check_payload())
        )
        self.assertEqual(check_response.status_code, 200)
        check_payload = check_response.json()
        self.assertTrue(check_payload["validation"]["valid"])
        self.assertEqual(check_payload["checkItems"][0]["state"], "accepted")


if __name__ == "__main__":
    unittest.main()
