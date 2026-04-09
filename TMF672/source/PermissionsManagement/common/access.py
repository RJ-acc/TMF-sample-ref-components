from __future__ import annotations

from typing import Any
from uuid import uuid4

from common.events import utc_now

DEFAULT_API_BASE_PATH = "/tmf-api/rolesAndPermissions/v4"
DEFAULT_SEED_TIMESTAMP = "2026-04-09T00:00:00Z"
ACCESS_STATES = {"granted", "active", "inactive", "revoked", "expired"}

RESOURCE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "permission": {
        "collection": "permissions",
        "type": "Permission",
        "id_prefix": "permission",
        "defaults": {},
    },
    "userRole": {
        "collection": "user_roles",
        "type": "UserRole",
        "id_prefix": "user-role",
        "defaults": {},
    },
}

RESOURCE_ORDER = ("permission", "userRole")
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
        raise KeyError(f"Unknown TMF672 resource '{resource_name}'") from exc


def resource_type(resource_name: str) -> str:
    return get_resource_definition(resource_name)["type"]


def resource_collection(resource_name: str) -> str:
    return get_resource_definition(resource_name)["collection"]


def resource_href(resource_name: str, entity_id: str, base_path: str = DEFAULT_API_BASE_PATH) -> str:
    return f"{base_path.rstrip('/')}/{resource_name}/{entity_id}"


def _permission_seed_documents(base_path: str) -> list[dict[str, Any]]:
    return [
        {
            "id": "permission-1001",
            "href": resource_href("permission", "permission-1001", base_path),
            "creationDate": DEFAULT_SEED_TIMESTAMP,
            "description": "Billing approval access granted to the regional finance supervisor.",
            "granter": {
                "id": "individual-9001",
                "name": "Avery Morgan",
                "role": "granter",
                "@referredType": "Individual",
            },
            "user": {
                "id": "individual-1001",
                "name": "Jordan Blake",
                "role": "user",
                "@referredType": "Individual",
            },
            "validFor": {
                "startDateTime": "2026-01-01T00:00:00Z",
                "endDateTime": "2026-12-31T23:59:59Z",
            },
            "assetUserRole": [
                {
                    "manageableAsset": {
                        "id": "billing-account-1001",
                        "name": "Northwind Billing Account",
                        "@referredType": "BillingAccount",
                    },
                    "userRole": {
                        "id": "user-role-1001",
                        "href": resource_href("userRole", "user-role-1001", base_path),
                        "@referredType": "UserRole",
                    },
                }
            ],
            "privilege": [
                {
                    "action": "approve",
                    "function": "invoiceAdjustment",
                    "manageableAsset": {
                        "id": "billing-account-1001",
                        "name": "Northwind Billing Account",
                        "@referredType": "BillingAccount",
                    },
                }
            ],
            "@type": "Permission",
            "lastUpdate": DEFAULT_SEED_TIMESTAMP,
        },
        {
            "id": "permission-1002",
            "href": resource_href("permission", "permission-1002", base_path),
            "creationDate": DEFAULT_SEED_TIMESTAMP,
            "description": "Read-only order access granted to the support desk lead.",
            "granter": {
                "id": "individual-9002",
                "name": "Mika Chen",
                "role": "granter",
                "@referredType": "Individual",
            },
            "user": {
                "id": "individual-1002",
                "name": "Taylor Brooks",
                "role": "user",
                "@referredType": "Individual",
            },
            "validFor": {
                "startDateTime": "2026-02-01T00:00:00Z",
                "endDateTime": "2026-09-30T23:59:59Z",
            },
            "assetUserRole": [
                {
                    "manageableAsset": {
                        "id": "product-order-2001",
                        "name": "Enterprise Upgrade Order",
                        "@referredType": "ProductOrder",
                    },
                    "userRole": {
                        "id": "user-role-1002",
                        "href": resource_href("userRole", "user-role-1002", base_path),
                        "@referredType": "UserRole",
                    },
                }
            ],
            "privilege": [
                {
                    "action": "read",
                    "function": "orderReview",
                    "manageableAsset": {
                        "id": "product-order-2001",
                        "name": "Enterprise Upgrade Order",
                        "@referredType": "ProductOrder",
                    },
                }
            ],
            "@type": "Permission",
            "lastUpdate": DEFAULT_SEED_TIMESTAMP,
        },
    ]


def _user_role_seed_documents(base_path: str) -> list[dict[str, Any]]:
    return [
        {
            "id": "user-role-1001",
            "href": resource_href("userRole", "user-role-1001", base_path),
            "involvementRole": "BillingSupervisor",
            "entitlement": [
                {"action": "read", "function": "invoiceReview", "@type": "Entitlement"},
                {"action": "approve", "function": "invoiceAdjustment", "@type": "Entitlement"},
            ],
            "@type": "UserRole",
            "lastUpdate": DEFAULT_SEED_TIMESTAMP,
        },
        {
            "id": "user-role-1002",
            "href": resource_href("userRole", "user-role-1002", base_path),
            "involvementRole": "SupportDeskLead",
            "entitlement": [
                {"action": "read", "function": "orderReview", "@type": "Entitlement"},
                {"action": "update", "function": "caseComment", "@type": "Entitlement"},
            ],
            "@type": "UserRole",
            "lastUpdate": DEFAULT_SEED_TIMESTAMP,
        },
    ]


def _seed_documents(base_path: str) -> dict[str, list[dict[str, Any]]]:
    return {
        "permissions": _permission_seed_documents(base_path),
        "user_roles": _user_role_seed_documents(base_path),
    }


def ensure_seed_data(store: Any, base_path: str = DEFAULT_API_BASE_PATH) -> None:
    if store.list_documents(resource_collection("permission"), limit=1):
        return

    seed_documents = _seed_documents(base_path)
    for metadata in RESOURCE_DEFINITIONS.values():
        collection = metadata["collection"]
        for document in seed_documents[collection]:
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
        "@type": payload.get("@type", metadata["type"]),
        "lastUpdate": utc_now(),
    }
    if resource_name == "permission":
        entity["creationDate"] = payload.get("creationDate", utc_now())
    return entity


def apply_patch(
    resource_name: str,
    existing: dict[str, Any],
    patch: dict[str, Any],
    base_path: str = DEFAULT_API_BASE_PATH,
) -> dict[str, Any]:
    updated = {
        **existing,
        **patch,
        "id": existing["id"],
        "href": resource_href(resource_name, existing["id"], base_path),
        "lastUpdate": utc_now(),
    }
    updated["@type"] = updated.get("@type", resource_type(resource_name))
    if resource_name == "permission":
        updated["creationDate"] = existing.get("creationDate") or patch.get("creationDate") or utc_now()
    return updated
