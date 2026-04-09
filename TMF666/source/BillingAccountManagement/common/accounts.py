from __future__ import annotations

from typing import Any
from uuid import uuid4

from common.events import utc_now

DEFAULT_API_BASE_PATH = "/tmf-api/accountManagement/v5"
DEFAULT_SEED_TIMESTAMP = "2026-04-08T00:00:00Z"
ACCOUNT_STATES = {
    "active",
    "inactive",
    "suspended",
    "closed",
    "pending",
}

RESOURCE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "billFormat": {
        "collection": "bill_formats",
        "type": "BillFormat",
        "id_prefix": "bill-format",
        "default_state": "active",
        "defaults": {
            "lifecycleStatus": "active",
            "isBinary": False,
        },
    },
    "billPresentationMedia": {
        "collection": "bill_presentation_media",
        "type": "BillPresentationMedia",
        "id_prefix": "bill-presentation-media",
        "default_state": "active",
        "defaults": {
            "mediumType": "email",
        },
    },
    "billingAccount": {
        "collection": "billing_accounts",
        "type": "BillingAccount",
        "id_prefix": "billing-account",
        "default_state": "active",
        "defaults": {
            "accountType": "customerBilling",
        },
    },
    "billingCycleSpecification": {
        "collection": "billing_cycle_specifications",
        "type": "BillingCycleSpecification",
        "id_prefix": "billing-cycle-spec",
        "default_state": "active",
        "defaults": {
            "frequency": "monthly",
        },
    },
    "financialAccount": {
        "collection": "financial_accounts",
        "type": "FinancialAccount",
        "id_prefix": "financial-account",
        "default_state": "active",
        "defaults": {
            "accountType": "receivable",
        },
    },
    "partyAccount": {
        "collection": "party_accounts",
        "type": "PartyAccount",
        "id_prefix": "party-account",
        "default_state": "active",
        "defaults": {
            "accountType": "customer",
        },
    },
    "settlementAccount": {
        "collection": "settlement_accounts",
        "type": "SettlementAccount",
        "id_prefix": "settlement-account",
        "default_state": "active",
        "defaults": {
            "accountType": "settlement",
        },
    },
}

RESOURCE_ORDER = tuple(RESOURCE_DEFINITIONS.keys())
LISTENER_EVENT_SUFFIXES = (
    "AttributeValueChangeEvent",
    "CreateEvent",
    "DeleteEvent",
    "StateChangeEvent",
)


def resource_names() -> tuple[str, ...]:
    return RESOURCE_ORDER


def listener_event_types() -> list[str]:
    return [
        f"{resource_type(resource_name)}{suffix}"
        for resource_name in RESOURCE_ORDER
        for suffix in LISTENER_EVENT_SUFFIXES
    ]


def get_resource_definition(resource_name: str) -> dict[str, Any]:
    try:
        return RESOURCE_DEFINITIONS[resource_name]
    except KeyError as exc:
        raise KeyError(f"Unknown TMF666 resource '{resource_name}'") from exc


def resource_type(resource_name: str) -> str:
    return get_resource_definition(resource_name)["type"]


def resource_collection(resource_name: str) -> str:
    return get_resource_definition(resource_name)["collection"]


def resource_href(resource_name: str, entity_id: str, base_path: str = DEFAULT_API_BASE_PATH) -> str:
    return f"{base_path.rstrip('/')}/{resource_name}/{entity_id}"


def _base_entity(
    resource_name: str,
    entity_id: str,
    name: str,
    base_path: str,
    **fields: Any,
) -> dict[str, Any]:
    metadata = get_resource_definition(resource_name)
    state = fields.pop("state", metadata["default_state"])
    status = fields.pop("status", state)
    return {
        **metadata["defaults"],
        **fields,
        "id": entity_id,
        "href": resource_href(resource_name, entity_id, base_path),
        "name": name,
        "state": state,
        "status": status,
        "lastUpdate": fields.pop("lastUpdate", DEFAULT_SEED_TIMESTAMP),
        "@type": metadata["type"],
    }


def _normalize_related_bill_format(document: dict[str, Any], base_path: str) -> None:
    if document.get("@type") != "BillPresentationMedia":
        return
    bill_format = document.get("billFormat")
    if not isinstance(bill_format, dict) or not bill_format.get("id"):
        return
    bill_format.setdefault("href", resource_href("billFormat", bill_format["id"], base_path))
    bill_format.setdefault("@type", "BillFormatRef")
    bill_format.setdefault("@referredType", "BillFormat")


def _seed_documents(base_path: str) -> dict[str, list[dict[str, Any]]]:
    return {
        "bill_formats": [
            _base_entity(
                "billFormat",
                "bill-format-email-pdf",
                "Email PDF",
                base_path,
                description="Portable document format delivered through email.",
                formatType="PDF",
            ),
            _base_entity(
                "billFormat",
                "bill-format-portal-html",
                "Portal HTML",
                base_path,
                description="Interactive HTML rendering for self-service billing portals.",
                formatType="HTML",
            ),
        ],
        "bill_presentation_media": [
            _base_entity(
                "billPresentationMedia",
                "bill-pm-email-001",
                "Email Delivery",
                base_path,
                description="Default email-based bill presentation preference.",
                billFormat={"id": "bill-format-email-pdf"},
                mediumType="email",
            ),
            _base_entity(
                "billPresentationMedia",
                "bill-pm-portal-001",
                "Portal Delivery",
                base_path,
                description="Bill presentation through a secure customer portal.",
                billFormat={"id": "bill-format-portal-html"},
                mediumType="portal",
            ),
        ],
        "billing_accounts": [
            _base_entity(
                "billingAccount",
                "billing-account-1001",
                "Northwind HQ Billing",
                base_path,
                description="Primary billing account for Northwind headquarters.",
                accountBalance={"amount": {"unit": "USD", "value": 182.45}},
                relatedParty=[{"id": "org-1001", "role": "customer", "@referredType": "Organization"}],
            ),
            _base_entity(
                "billingAccount",
                "billing-account-1002",
                "Contoso West Billing",
                base_path,
                description="Regional billing account for Contoso West.",
                accountBalance={"amount": {"unit": "USD", "value": 74.2}},
                relatedParty=[{"id": "org-1002", "role": "customer", "@referredType": "Organization"}],
            ),
        ],
        "billing_cycle_specifications": [
            _base_entity(
                "billingCycleSpecification",
                "billing-cycle-spec-monthly",
                "Monthly Billing Cycle",
                base_path,
                description="Standard monthly billing cadence.",
                frequency="monthly",
                billingDateShift=0,
            ),
            _base_entity(
                "billingCycleSpecification",
                "billing-cycle-spec-quarterly",
                "Quarterly Billing Cycle",
                base_path,
                description="Quarterly billing cadence for enterprise customers.",
                frequency="quarterly",
                billingDateShift=5,
            ),
        ],
        "financial_accounts": [
            _base_entity(
                "financialAccount",
                "financial-account-1001",
                "Receivables Ledger 1001",
                base_path,
                description="Receivables ledger backing Northwind billing.",
                accountBalance={"amount": {"unit": "USD", "value": 182.45}},
            ),
            _base_entity(
                "financialAccount",
                "financial-account-1002",
                "Receivables Ledger 1002",
                base_path,
                description="Receivables ledger backing Contoso West billing.",
                accountBalance={"amount": {"unit": "USD", "value": 74.2}},
            ),
        ],
        "party_accounts": [
            _base_entity(
                "partyAccount",
                "party-account-1001",
                "Northwind Party Account",
                base_path,
                description="Commercial party account linked to Northwind.",
                relatedParty=[{"id": "org-1001", "role": "customer", "@referredType": "Organization"}],
            ),
            _base_entity(
                "partyAccount",
                "party-account-1002",
                "Contoso Party Account",
                base_path,
                description="Commercial party account linked to Contoso West.",
                relatedParty=[{"id": "org-1002", "role": "customer", "@referredType": "Organization"}],
            ),
        ],
        "settlement_accounts": [
            _base_entity(
                "settlementAccount",
                "settlement-account-1001",
                "Settlement Account East",
                base_path,
                description="Settlement account for East region payouts.",
                defaultPaymentMethod="bankTransfer",
            ),
            _base_entity(
                "settlementAccount",
                "settlement-account-1002",
                "Settlement Account West",
                base_path,
                description="Settlement account for West region payouts.",
                defaultPaymentMethod="directDebit",
            ),
        ],
    }


def ensure_seed_data(store: Any, base_path: str = DEFAULT_API_BASE_PATH) -> None:
    if store.list_documents(resource_collection("billingAccount"), limit=1):
        return

    seed_documents = _seed_documents(base_path)
    for metadata in RESOURCE_DEFINITIONS.values():
        collection = metadata["collection"]
        for document in seed_documents[collection]:
            _normalize_related_bill_format(document, base_path)
            try:
                store.create_document(collection, document)
            except ValueError:
                continue


def build_entity(resource_name: str, payload: dict[str, Any], base_path: str = DEFAULT_API_BASE_PATH) -> dict[str, Any]:
    metadata = get_resource_definition(resource_name)
    entity_id = payload.get("id") or f"{metadata['id_prefix']}-{uuid4().hex[:8]}"
    entity = {
        **metadata["defaults"],
        **payload,
        "id": entity_id,
        "href": resource_href(resource_name, entity_id, base_path),
        "name": payload.get("name") or f"{metadata['type']} {entity_id}",
        "state": payload.get("state", metadata["default_state"]),
        "status": payload.get("status", payload.get("state", metadata["default_state"])),
        "lastUpdate": utc_now(),
        "@type": payload.get("@type", metadata["type"]),
    }
    _normalize_related_bill_format(entity, base_path)
    return entity


def apply_patch(
    resource_name: str,
    existing: dict[str, Any],
    patch: dict[str, Any],
    base_path: str = DEFAULT_API_BASE_PATH,
) -> dict[str, Any]:
    metadata = get_resource_definition(resource_name)
    updated = {
        **existing,
        **patch,
        "id": existing["id"],
        "href": resource_href(resource_name, existing["id"], base_path),
        "state": patch.get("state", existing.get("state", metadata["default_state"])),
        "status": patch.get(
            "status",
            patch.get("state", existing.get("status", existing.get("state", metadata["default_state"]))),
        ),
        "lastUpdate": utc_now(),
        "@type": existing.get("@type", metadata["type"]),
    }
    _normalize_related_bill_format(updated, base_path)
    return updated
