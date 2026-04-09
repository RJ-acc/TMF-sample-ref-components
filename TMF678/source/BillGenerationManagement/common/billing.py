from __future__ import annotations

import copy
from datetime import UTC, datetime, timedelta
from typing import Any

from common.events import utc_now
from common.validation import validate_customer_bill_on_demand

STARTER_BILL_CYCLES = [
    {
        "id": "monthly-01",
        "href": "/tmf-api/customerBillManagement/v5/billCycle/monthly-01",
        "name": "Monthly cycle",
        "frequency": "monthly",
        "billingDateShift": 0,
        "mailingDateShift": 1,
        "validFor": {
            "startDateTime": "2026-01-01T00:00:00Z",
            "endDateTime": "2026-12-31T23:59:59Z",
        },
        "@type": "BillCycle",
    },
    {
        "id": "quarterly-01",
        "href": "/tmf-api/customerBillManagement/v5/billCycle/quarterly-01",
        "name": "Quarterly cycle",
        "frequency": "quarterly",
        "billingDateShift": 0,
        "mailingDateShift": 2,
        "validFor": {
            "startDateTime": "2026-01-01T00:00:00Z",
            "endDateTime": "2026-12-31T23:59:59Z",
        },
        "@type": "BillCycle",
    },
]

STARTER_APPLIED_CUSTOMER_BILLING_RATES = [
    {
        "id": "rate-1001",
        "href": "/tmf-api/customerBillManagement/v5/appliedCustomerBillingRate/rate-1001",
        "name": "Fiber access charge",
        "description": "Recurring charge for the enterprise fiber product.",
        "billingAccount": {"id": "acct-100", "name": "Northwind HQ", "@type": "BillingAccountRef"},
        "product": {"id": "prod-100", "name": "Enterprise Fiber", "@type": "ProductRef"},
        "taxExcludedAmount": {"unit": "USD", "value": 180},
        "taxIncludedAmount": {"unit": "USD", "value": 198},
        "periodCoverage": {"startDateTime": "2026-03-01T00:00:00Z", "endDateTime": "2026-03-31T23:59:59Z"},
        "billCycle": {"id": "monthly-01", "name": "Monthly cycle", "@type": "BillCycleRef"},
        "@type": "AppliedCustomerBillingRate",
    },
    {
        "id": "rate-1002",
        "href": "/tmf-api/customerBillManagement/v5/appliedCustomerBillingRate/rate-1002",
        "name": "Managed router service",
        "description": "Managed service fee for the enterprise router.",
        "billingAccount": {"id": "acct-100", "name": "Northwind HQ", "@type": "BillingAccountRef"},
        "product": {"id": "prod-101", "name": "Managed Router", "@type": "ProductRef"},
        "taxExcludedAmount": {"unit": "USD", "value": 45},
        "taxIncludedAmount": {"unit": "USD", "value": 49.5},
        "periodCoverage": {"startDateTime": "2026-03-01T00:00:00Z", "endDateTime": "2026-03-31T23:59:59Z"},
        "billCycle": {"id": "monthly-01", "name": "Monthly cycle", "@type": "BillCycleRef"},
        "@type": "AppliedCustomerBillingRate",
    },
    {
        "id": "rate-2001",
        "href": "/tmf-api/customerBillManagement/v5/appliedCustomerBillingRate/rate-2001",
        "name": "Business mobile plan",
        "description": "Monthly recurring charge for the mobile plan.",
        "billingAccount": {"id": "acct-200", "name": "Fabrikam Field Team", "@type": "BillingAccountRef"},
        "product": {"id": "prod-200", "name": "Business Mobile", "@type": "ProductRef"},
        "taxExcludedAmount": {"unit": "USD", "value": 72},
        "taxIncludedAmount": {"unit": "USD", "value": 79.2},
        "periodCoverage": {"startDateTime": "2026-03-01T00:00:00Z", "endDateTime": "2026-03-31T23:59:59Z"},
        "billCycle": {"id": "monthly-01", "name": "Monthly cycle", "@type": "BillCycleRef"},
        "@type": "AppliedCustomerBillingRate",
    },
]


def _money(amount: float, currency: str = "USD") -> dict[str, Any]:
    return {"unit": currency, "value": round(amount, 2)}


def _bill_ref(bill_id: str, name: str) -> dict[str, Any]:
    return {
        "id": bill_id,
        "href": f"/tmf-api/customerBillManagement/v5/customerBill/{bill_id}",
        "name": name,
        "@referredType": "CustomerBill",
        "@type": "CustomerBillRef",
    }


def _today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def _plus_days(days: int) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).strftime("%Y-%m-%d")


def _account_ref(account_id: str, account_name: str) -> dict[str, Any]:
    return {
        "id": account_id,
        "name": account_name,
        "@type": "BillingAccountRef",
    }


def _bill_cycle_ref(cycle: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": cycle["id"],
        "name": cycle["name"],
        "@type": "BillCycleRef",
    }


def _rates_for_account(account_id: str, cycle_id: str | None = None) -> list[dict[str, Any]]:
    rates = []
    for rate in STARTER_APPLIED_CUSTOMER_BILLING_RATES:
        if rate["billingAccount"]["id"] != account_id:
            continue
        if cycle_id and rate.get("billCycle", {}).get("id") != cycle_id:
            continue
        rates.append(copy.deepcopy(rate))
    return rates


def _build_customer_bill(
    *,
    bill_id: str,
    account_id: str,
    account_name: str,
    cycle: dict[str, Any],
    rates: list[dict[str, Any]],
    bill_date: str,
    status: str = "issued",
) -> dict[str, Any]:
    total_tax_excluded = sum(float(rate["taxExcludedAmount"]["value"]) for rate in rates)
    total_tax_included = sum(float(rate["taxIncludedAmount"]["value"]) for rate in rates)
    name = f"Customer bill {bill_id}"

    return {
        "id": bill_id,
        "href": f"/tmf-api/customerBillManagement/v5/customerBill/{bill_id}",
        "name": name,
        "state": status,
        "billNo": bill_id.upper(),
        "billDate": bill_date,
        "paymentDueDate": _plus_days(14),
        "billingAccount": _account_ref(account_id, account_name),
        "billCycle": _bill_cycle_ref(cycle),
        "amountDue": _money(total_tax_included),
        "remainingAmount": _money(total_tax_included),
        "taxExcludedAmount": _money(total_tax_excluded),
        "taxIncludedAmount": _money(total_tax_included),
        "appliedCustomerBillingRate": [
            {
                "id": rate["id"],
                "href": rate["href"],
                "name": rate["name"],
                "@referredType": "AppliedCustomerBillingRate",
                "@type": "AppliedCustomerBillingRateRef",
            }
            for rate in rates
        ],
        "lastUpdate": utc_now(),
        "@type": "CustomerBill",
    }


STARTER_CUSTOMER_BILLS = [
    _build_customer_bill(
        bill_id="bill-1001",
        account_id="acct-100",
        account_name="Northwind HQ",
        cycle=STARTER_BILL_CYCLES[0],
        rates=_rates_for_account("acct-100", "monthly-01"),
        bill_date="2026-03-31",
        status="issued",
    ),
    _build_customer_bill(
        bill_id="bill-2001",
        account_id="acct-200",
        account_name="Fabrikam Field Team",
        cycle=STARTER_BILL_CYCLES[0],
        rates=_rates_for_account("acct-200", "monthly-01"),
        bill_date="2026-03-31",
        status="delivered",
    ),
]


def ensure_seed_data(store: Any) -> None:
    if not store.list_documents("bill_cycles"):
        for cycle in STARTER_BILL_CYCLES:
            store.create_document("bill_cycles", cycle)

    if not store.list_documents("applied_customer_billing_rates"):
        for rate in STARTER_APPLIED_CUSTOMER_BILLING_RATES:
            store.create_document("applied_customer_billing_rates", rate)

    if not store.list_documents("customer_bills"):
        for bill in STARTER_CUSTOMER_BILLS:
            store.create_document("customer_bills", bill)


def list_bill_cycles() -> list[dict[str, Any]]:
    return copy.deepcopy(STARTER_BILL_CYCLES)


def list_applied_customer_billing_rates() -> list[dict[str, Any]]:
    return copy.deepcopy(STARTER_APPLIED_CUSTOMER_BILLING_RATES)


def generate_customer_bill_on_demand(payload: dict[str, Any]) -> dict[str, Any]:
    validation = validate_customer_bill_on_demand(payload)
    if not validation["valid"]:
        return {
            "validation": validation,
            "customerBillOnDemand": None,
            "customerBill": None,
            "summary": {
                "generated": False,
                "reason": "validationFailed",
            },
        }

    billing_account = payload["billingAccount"]
    cycle_id = (payload.get("billCycle") or {}).get("id") or STARTER_BILL_CYCLES[0]["id"]
    cycle = next((entry for entry in STARTER_BILL_CYCLES if entry["id"] == cycle_id), STARTER_BILL_CYCLES[0])
    account_id = billing_account["id"]
    account_name = billing_account.get("name") or account_id
    rates = _rates_for_account(account_id, cycle["id"])

    if not rates:
        rates = _rates_for_account("acct-100", cycle["id"])

    bill_suffix = payload.get("id") or "ondemand"
    bill_id = f"cb-{bill_suffix}"
    bill_date = payload.get("billDate") or _today()
    generated_bill = _build_customer_bill(
        bill_id=bill_id,
        account_id=account_id,
        account_name=account_name,
        cycle=cycle,
        rates=rates,
        bill_date=bill_date,
        status="issued",
    )

    on_demand = {
        **payload,
        "href": f"/tmf-api/customerBillManagement/v5/customerBillOnDemand/{payload.get('id', '')}".rstrip("/"),
        "state": payload.get("state", "done"),
        "billDate": bill_date,
        "billCycle": _bill_cycle_ref(cycle),
        "billingAccount": _account_ref(account_id, account_name),
        "customerBill": _bill_ref(generated_bill["id"], generated_bill["name"]),
        "lastUpdate": utc_now(),
        "@type": payload.get("@type", "CustomerBillOnDemand"),
    }

    return {
        "validation": validation,
        "customerBillOnDemand": on_demand,
        "customerBill": generated_bill,
        "summary": {
            "generated": True,
            "generatedCustomerBillId": generated_bill["id"],
            "appliedRateCount": len(rates),
            "amountDue": generated_bill["amountDue"],
        },
    }


def apply_customer_bill_patch(existing: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    updated = copy.deepcopy(existing)
    for key, value in patch.items():
        if key == "note" and isinstance(value, list):
            updated["note"] = value
            continue
        updated[key] = value

    updated["id"] = existing["id"]
    updated["href"] = existing["href"]
    updated["lastUpdate"] = utc_now()
    updated["@type"] = updated.get("@type", "CustomerBill")
    return updated
