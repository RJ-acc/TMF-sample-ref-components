from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path

import httpx

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from catalogManagementEngineMicroservice.implementation.app import app as engine_app
from common.catalog import crud_resource_names, resource_names, task_resource_names
from common.store import get_store
from productCatalogManagementMicroservice.implementation.app import LISTENER_OPERATIONS, app

API_BASE = "/tmf-api/productCatalogManagement/v5"


def sample_payloads() -> dict[str, dict]:
    return {
        "productCatalog": {
            "name": "Partner Marketplace Catalog",
            "description": "Catalog for partner marketplace offers",
            "version": "2026.04",
            "@type": "ProductCatalog",
        },
        "category": {
            "name": "Marketplace Bundles",
            "description": "Category for cross-sell bundle offers",
            "isRoot": False,
            "productCatalog": {"id": "product-catalog-retail"},
            "@type": "Category",
        },
        "productOffering": {
            "name": "Fiber 250 Promo",
            "description": "Promotional fiber offer with 250 Mbps profile",
            "isSellable": True,
            "productCatalog": {"id": "product-catalog-retail"},
            "category": [{"id": "category-broadband"}],
            "productSpecification": {"id": "product-specification-fiber-100"},
            "@type": "ProductOffering",
        },
        "productOfferingPrice": {
            "name": "Fiber 250 Promo Monthly Price",
            "description": "Recurring monthly price for the Fiber 250 promo offer",
            "priceType": "recurring",
            "recurringChargePeriod": "month",
            "price": {"taxIncludedAmount": {"unit": "USD", "value": 79.99}},
            "productOffering": {"id": "product-offering-fiber-100"},
            "@type": "ProductOfferingPrice",
        },
        "productSpecification": {
            "name": "Fiber 250",
            "description": "Fiber product specification with 250 Mbps target profile",
            "brand": "Contoso Fiber",
            "productNumber": "FIBER-250",
            "productCatalog": [{"id": "product-catalog-retail"}],
            "@type": "ProductSpecification",
        },
        "importJob": {
            "name": "Spring Catalog Import",
            "description": "Import a partner spring catalog payload",
            "contentType": "application/json",
            "url": "https://catalog.example.com/imports/spring-catalog.json",
            "state": "inProgress",
            "@type": "ImportJob",
        },
        "exportJob": {
            "name": "Spring Catalog Export",
            "description": "Export retail catalog content for partner sync",
            "contentType": "application/json",
            "url": "https://catalog.example.com/exports/spring-catalog.json",
            "state": "inProgress",
            "@type": "ExportJob",
        },
    }


class ProductCatalogManagementApiTest(unittest.TestCase):
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

    def test_api_directory_lists_resource_and_listener_paths(self) -> None:
        response = asyncio.run(self.request("GET", API_BASE))
        self.assertEqual(response.status_code, 200)
        links = response.json()["_links"]

        self.assertIn("registerListener", links)
        self.assertIn("unregisterListener", links)
        self.assertIn("listProductCatalog", links)
        self.assertIn("createProductCatalog", links)
        self.assertIn("retrieveProductCatalog", links)
        self.assertIn("patchProductCatalog", links)
        self.assertIn("deleteProductCatalog", links)
        self.assertIn("listImportJob", links)
        self.assertIn("createImportJob", links)
        self.assertIn("retrieveImportJob", links)
        self.assertNotIn("patchImportJob", links)
        self.assertIn("deleteImportJob", links)
        for operation_name, _ in LISTENER_OPERATIONS:
            self.assertIn(operation_name, links)

    def test_main_resources_support_full_crud(self) -> None:
        payloads = sample_payloads()
        for resource_name in crud_resource_names():
            payload = payloads[resource_name]
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
                    self.request("GET", f"{API_BASE}/{resource_name}/{entity['id']}", params={"fields": "id,name,state"})
                )
                self.assertEqual(retrieve_response.status_code, 200)
                self.assertEqual(retrieve_response.json()["id"], entity["id"])

                patch_response = asyncio.run(
                    self.request(
                        "PATCH",
                        f"{API_BASE}/{resource_name}/{entity['id']}",
                        json={"description": f"patched {resource_name}", "state": "inactive"},
                    )
                )
                self.assertEqual(patch_response.status_code, 200, patch_response.text)
                self.assertEqual(patch_response.json()["state"], "inactive")

                delete_response = asyncio.run(self.request("DELETE", f"{API_BASE}/{resource_name}/{entity['id']}"))
                self.assertEqual(delete_response.status_code, 204)

                missing_response = asyncio.run(self.request("GET", f"{API_BASE}/{resource_name}/{entity['id']}"))
                self.assertEqual(missing_response.status_code, 404)

    def test_product_offering_accepts_inline_price_refs(self) -> None:
        payload = {
            **sample_payloads()["productOffering"],
            "productOfferingPrice": [
                {
                    "@type": "ProductOfferingPriceRef",
                    "id": "product-offering-price-fiber-100-monthly",
                    "name": "Fiber 100 Monthly Price",
                }
            ],
        }

        response = asyncio.run(self.request("POST", f"{API_BASE}/productOffering", json=payload))

        self.assertEqual(response.status_code, 201, response.text)
        entity = response.json()
        price_ref = entity["productOfferingPrice"][0]
        self.assertEqual(price_ref["id"], "product-offering-price-fiber-100-monthly")
        self.assertEqual(price_ref["name"], "Fiber 100 Monthly Price")
        self.assertEqual(price_ref["@referredType"], "ProductOfferingPrice")
        self.assertTrue(price_ref["href"].endswith("/productOfferingPrice/product-offering-price-fiber-100-monthly"))

    def test_task_resources_support_list_create_retrieve_delete(self) -> None:
        payloads = sample_payloads()
        for resource_name in task_resource_names():
            payload = payloads[resource_name]
            with self.subTest(resource=resource_name):
                list_response = asyncio.run(self.request("GET", f"{API_BASE}/{resource_name}"))
                self.assertEqual(list_response.status_code, 200)
                self.assertGreaterEqual(len(list_response.json()), 2)

                create_response = asyncio.run(self.request("POST", f"{API_BASE}/{resource_name}", json=payload))
                self.assertEqual(create_response.status_code, 201, create_response.text)
                entity = create_response.json()
                self.assertEqual(entity["@type"], payload["@type"])

                retrieve_response = asyncio.run(
                    self.request("GET", f"{API_BASE}/{resource_name}/{entity['id']}", params={"fields": "id,name,state"})
                )
                self.assertEqual(retrieve_response.status_code, 200)
                self.assertEqual(retrieve_response.json()["id"], entity["id"])

                patch_response = asyncio.run(
                    self.request(
                        "PATCH",
                        f"{API_BASE}/{resource_name}/{entity['id']}",
                        json={"state": "completed"},
                    )
                )
                self.assertEqual(patch_response.status_code, 405)

                delete_response = asyncio.run(self.request("DELETE", f"{API_BASE}/{resource_name}/{entity['id']}"))
                self.assertEqual(delete_response.status_code, 204)

    def test_list_filters_fields_and_pagination(self) -> None:
        response = asyncio.run(
            self.request(
                "GET",
                f"{API_BASE}/productOffering",
                params={"fields": "id,name", "offset": 0, "limit": 1},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(sorted(response.json()[0].keys()), ["id", "name"])
        self.assertEqual(response.headers["X-Result-Count"], "1")

    def test_invalid_payloads_are_rejected(self) -> None:
        invalid_create = asyncio.run(
            self.request(
                "POST",
                f"{API_BASE}/productOffering",
                json={"name": "broken", "productSpecification": "not-an-object"},
            )
        )
        self.assertEqual(invalid_create.status_code, 400)
        self.assertFalse(invalid_create.json()["detail"]["valid"])

        invalid_task_create = asyncio.run(
            self.request(
                "POST",
                f"{API_BASE}/exportJob",
                json={"name": "broken", "contentType": ["application/json"]},
            )
        )
        self.assertEqual(invalid_task_create.status_code, 400)
        self.assertFalse(invalid_task_create.json()["detail"]["valid"])

        invalid_patch = asyncio.run(
            self.request(
                "PATCH",
                f"{API_BASE}/productCatalog/product-catalog-retail",
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
        payload = {"callback": "http://listener.local/events", "query": "eventType=ProductCatalogCreateEvent"}

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
        payloads = sample_payloads()
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

        for resource_name in crud_resource_names():
            with self.subTest(resource=f"{resource_name}-patch"):
                validate_patch = asyncio.run(
                    self.engine_request("POST", f"/validate/{resource_name}/patch", json={"state": "inactive"})
                )
                self.assertEqual(validate_patch.status_code, 200)
                self.assertTrue(validate_patch.json()["valid"])


if __name__ == "__main__":
    unittest.main()
