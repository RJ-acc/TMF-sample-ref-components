from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path

import httpx

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from billGenerationEngineMicroservice.implementation.app import app as engine_app
from billGenerationManagementMicroservice.implementation.app import app
from common.store import get_store


def sample_on_demand_payload() -> dict:
    return {
        "name": "Generate bill for Northwind HQ",
        "instantSync": True,
        "channel": {"id": "web", "name": "Web", "@type": "ChannelRef"},
        "relatedParty": [{"id": "cust-100", "role": "customer", "@referredType": "Organization"}],
        "billingAccount": {"id": "acct-100", "name": "Northwind HQ", "@type": "BillingAccountRef"},
        "billCycle": {"id": "monthly-01", "name": "Monthly cycle", "@type": "BillCycleRef"},
        "billDate": "2026-04-08",
        "@type": "CustomerBillOnDemand",
    }


class BillGenerationManagementApiTest(unittest.TestCase):
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

    def test_read_only_catalog_paths(self) -> None:
        applied_rates = asyncio.run(self.request("GET", "/tmf-api/customerBillManagement/v5/appliedCustomerBillingRate"))
        self.assertEqual(applied_rates.status_code, 200)
        self.assertGreaterEqual(len(applied_rates.json()), 2)
        self.assertEqual(applied_rates.headers["X-Total-Count"], str(len(applied_rates.json())))

        applied_rate = asyncio.run(
            self.request(
                "GET",
                "/tmf-api/customerBillManagement/v5/appliedCustomerBillingRate/rate-1001",
                params={"fields": "id,name"},
            )
        )
        self.assertEqual(applied_rate.status_code, 200)
        self.assertEqual(applied_rate.json()["id"], "rate-1001")

        bill_cycles = asyncio.run(self.request("GET", "/tmf-api/customerBillManagement/v5/billCycle"))
        self.assertEqual(bill_cycles.status_code, 200)
        self.assertGreaterEqual(len(bill_cycles.json()), 2)

        bill_cycle = asyncio.run(
            self.request("GET", "/tmf-api/customerBillManagement/v5/billCycle/monthly-01", params={"fields": "id,name"})
        )
        self.assertEqual(bill_cycle.status_code, 200)
        self.assertEqual(bill_cycle.json(), {"id": "monthly-01", "name": "Monthly cycle"})

    def test_customer_bill_list_retrieve_and_patch(self) -> None:
        list_response = asyncio.run(self.request("GET", "/tmf-api/customerBillManagement/v5/customerBill"))
        self.assertEqual(list_response.status_code, 200)
        self.assertGreaterEqual(len(list_response.json()), 2)

        retrieve_response = asyncio.run(
            self.request("GET", "/tmf-api/customerBillManagement/v5/customerBill/bill-1001", params={"fields": "id,state"})
        )
        self.assertEqual(retrieve_response.status_code, 200)
        self.assertEqual(retrieve_response.json()["state"], "issued")

        patch_response = asyncio.run(
            self.request(
                "PATCH",
                "/tmf-api/customerBillManagement/v5/customerBill/bill-1001",
                json={"state": "settled"},
            )
        )
        self.assertEqual(patch_response.status_code, 200, patch_response.text)
        self.assertEqual(patch_response.json()["state"], "settled")

    def test_customer_bill_on_demand_create_list_and_retrieve(self) -> None:
        create_response = asyncio.run(
            self.request(
                "POST",
                "/tmf-api/customerBillManagement/v5/customerBillOnDemand",
                json=sample_on_demand_payload(),
            )
        )
        self.assertEqual(create_response.status_code, 200, create_response.text)
        entity = create_response.json()
        self.assertEqual(entity["state"], "done")
        self.assertEqual(entity["customerBill"]["@referredType"], "CustomerBill")

        list_response = asyncio.run(self.request("GET", "/tmf-api/customerBillManagement/v5/customerBillOnDemand"))
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)

        retrieve_response = asyncio.run(
            self.request(
                "GET",
                f"/tmf-api/customerBillManagement/v5/customerBillOnDemand/{entity['id']}",
                params={"fields": "id,state"},
            )
        )
        self.assertEqual(retrieve_response.status_code, 200)
        self.assertEqual(retrieve_response.json(), {"id": entity["id"], "state": "done"})

        generated_bill = asyncio.run(
            self.request("GET", f"/tmf-api/customerBillManagement/v5/customerBill/{entity['customerBill']['id']}")
        )
        self.assertEqual(generated_bill.status_code, 200)

    def test_invalid_on_demand_payload_is_persisted_with_error_state(self) -> None:
        payload = sample_on_demand_payload()
        payload["billingAccount"] = "broken"

        response = asyncio.run(
            self.request("POST", "/tmf-api/customerBillManagement/v5/customerBillOnDemand", json=payload)
        )
        self.assertEqual(response.status_code, 200, response.text)
        entity = response.json()
        self.assertEqual(entity["state"], "terminatedWithError")
        self.assertFalse(entity["validationResult"]["valid"])

    def test_patch_and_delete_are_only_exposed_where_tmf678_allows(self) -> None:
        on_demand_response = asyncio.run(
            self.request("POST", "/tmf-api/customerBillManagement/v5/customerBillOnDemand", json=sample_on_demand_payload())
        )
        on_demand_id = on_demand_response.json()["id"]

        post_customer_bill = asyncio.run(self.request("POST", "/tmf-api/customerBillManagement/v5/customerBill", json={}))
        self.assertEqual(post_customer_bill.status_code, 405)

        delete_customer_bill = asyncio.run(
            self.request("DELETE", "/tmf-api/customerBillManagement/v5/customerBill/bill-1001")
        )
        self.assertEqual(delete_customer_bill.status_code, 405)

        patch_on_demand = asyncio.run(
            self.request("PATCH", f"/tmf-api/customerBillManagement/v5/customerBillOnDemand/{on_demand_id}", json={})
        )
        self.assertEqual(patch_on_demand.status_code, 405)

        delete_on_demand = asyncio.run(
            self.request("DELETE", f"/tmf-api/customerBillManagement/v5/customerBillOnDemand/{on_demand_id}")
        )
        self.assertEqual(delete_on_demand.status_code, 405)

        post_applied_rate = asyncio.run(
            self.request("POST", "/tmf-api/customerBillManagement/v5/appliedCustomerBillingRate", json={})
        )
        self.assertEqual(post_applied_rate.status_code, 405)

        patch_bill_cycle = asyncio.run(
            self.request("PATCH", "/tmf-api/customerBillManagement/v5/billCycle/monthly-01", json={})
        )
        self.assertEqual(patch_bill_cycle.status_code, 405)

    def test_register_listener_is_idempotent_and_unregistration_works(self) -> None:
        payload = {"callback": "http://listener.local/events", "query": "eventType=CustomerBillCreateEvent"}

        first = asyncio.run(self.request("POST", "/tmf-api/customerBillManagement/v5/hub", json=payload))
        second = asyncio.run(self.request("POST", "/tmf-api/customerBillManagement/v5/hub", json=payload))

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.json()["id"], second.json()["id"])

        delete_response = asyncio.run(
            self.request("DELETE", f"/tmf-api/customerBillManagement/v5/hub/{first.json()['id']}")
        )
        self.assertEqual(delete_response.status_code, 204)

    def test_all_listener_endpoints_acknowledge(self) -> None:
        listener_paths = [
            "/tmf-api/customerBillManagement/v5/listener/customerBillCreateEvent",
            "/tmf-api/customerBillManagement/v5/listener/customerBillOnDemandCreateEvent",
            "/tmf-api/customerBillManagement/v5/listener/customerBillOnDemandStateChangeEvent",
            "/tmf-api/customerBillManagement/v5/listener/customerBillStateChangeEvent",
        ]
        for path in listener_paths:
            response = asyncio.run(self.request("POST", path, json={"eventType": path.rsplit("/", 1)[-1]}))
            self.assertEqual(response.status_code, 204, path)

    def test_engine_paths(self) -> None:
        bill_cycle_response = asyncio.run(self.engine_request("GET", "/billCycle"))
        self.assertEqual(bill_cycle_response.status_code, 200)
        self.assertGreaterEqual(bill_cycle_response.json()["count"], 2)

        rate_response = asyncio.run(self.engine_request("GET", "/appliedCustomerBillingRate"))
        self.assertEqual(rate_response.status_code, 200)
        self.assertGreaterEqual(rate_response.json()["count"], 2)

        validate_on_demand = asyncio.run(
            self.engine_request("POST", "/validate/customerBillOnDemand", json=sample_on_demand_payload())
        )
        self.assertEqual(validate_on_demand.status_code, 200)
        self.assertTrue(validate_on_demand.json()["valid"])

        validate_patch = asyncio.run(
            self.engine_request("POST", "/validate/customerBillPatch", json={"state": "settled"})
        )
        self.assertEqual(validate_patch.status_code, 200)
        self.assertTrue(validate_patch.json()["valid"])

        generate_on_demand = asyncio.run(
            self.engine_request("POST", "/generate/customerBillOnDemand", json=sample_on_demand_payload())
        )
        self.assertEqual(generate_on_demand.status_code, 200)
        self.assertTrue(generate_on_demand.json()["summary"]["generated"])


if __name__ == "__main__":
    unittest.main()
