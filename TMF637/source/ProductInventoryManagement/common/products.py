from __future__ import annotations

from typing import Any
from uuid import uuid4

from common.events import utc_now

DEFAULT_API_BASE_PATH = "/tmf-api/productInventoryManagement/v5"
DEFAULT_SEED_TIMESTAMP = "2026-04-09T00:00:00Z"
PRODUCT_STATUSES = {
    "created",
    "pendingActive",
    "cancelled",
    "active",
    "pendingTerminate",
    "terminated",
    "suspended",
    "aborted",
}

RESOURCE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "product": {
        "collection": "products",
        "type": "Product",
        "id_prefix": "product",
        "default_status": "created",
    }
}

RESOURCE_ORDER = ("product",)
LISTENER_EVENT_SUFFIXES = (
    "AttributeValueChangeEvent",
    "CreateEvent",
    "DeleteEvent",
    "ProductBatchEvent",
    "StateChangeEvent",
)


def resource_names() -> tuple[str, ...]:
    return RESOURCE_ORDER


def listener_event_types() -> list[str]:
    return [f"{resource_type(resource_name)}{suffix}" for resource_name in RESOURCE_ORDER for suffix in LISTENER_EVENT_SUFFIXES]


def get_resource_definition(resource_name: str) -> dict[str, Any]:
    try:
        return RESOURCE_DEFINITIONS[resource_name]
    except KeyError as exc:
        raise KeyError(f"Unknown TMF637 resource '{resource_name}'") from exc


def resource_type(resource_name: str) -> str:
    return get_resource_definition(resource_name)["type"]


def resource_collection(resource_name: str) -> str:
    return get_resource_definition(resource_name)["collection"]


def resource_href(resource_name: str, entity_id: str, base_path: str = DEFAULT_API_BASE_PATH) -> str:
    return f"{base_path.rstrip('/')}/{resource_name}/{entity_id}"


def _party(role: str, party_id: str, party_name: str, referred_type: str = "Individual") -> dict[str, Any]:
    return {
        "@type": "RelatedPartyOrPartyRole",
        "role": role,
        "id": party_id,
        "name": party_name,
        "@referredType": referred_type,
    }


def _ref(entity_type: str, entity_id: str, name: str) -> dict[str, Any]:
    return {
        "@type": f"{entity_type}Ref",
        "id": entity_id,
        "name": name,
        "@referredType": entity_type,
    }


def _characteristic(name: str, value: str) -> dict[str, Any]:
    return {
        "@type": "StringCharacteristic",
        "name": name,
        "value": value,
    }


def _note(author: str, text: str) -> dict[str, Any]:
    return {
        "@type": "Note",
        "author": author,
        "date": DEFAULT_SEED_TIMESTAMP,
        "text": text,
    }


def _base_entity(entity_id: str, base_path: str, **fields: Any) -> dict[str, Any]:
    metadata = get_resource_definition("product")
    status = fields.pop("status", metadata["default_status"])
    creation_date = fields.pop("creationDate", DEFAULT_SEED_TIMESTAMP)
    last_update = fields.pop("lastUpdate", creation_date)
    status_change_date = fields.pop("statusChangeDate", last_update)
    return {
        **fields,
        "id": entity_id,
        "href": resource_href("product", entity_id, base_path),
        "status": status,
        "creationDate": creation_date,
        "lastUpdate": last_update,
        "statusChangeDate": status_change_date,
        "@type": "Product",
    }


def _seed_documents(base_path: str) -> dict[str, list[dict[str, Any]]]:
    return {
        "products": [
            _base_entity(
                "product-fiber-1001",
                base_path,
                name="Fiber 100 Access",
                description="Residential fiber access product with 100 Mbps downstream profile.",
                status="active",
                isBundle=False,
                isCustomerVisible=True,
                startDate="2026-04-07T09:00:00Z",
                productSerialNumber="ONT-100-1001",
                productOffering=_ref("ProductOffering", "product-offering-fiber-100", "Fiber 100"),
                productSpecification=_ref("ProductSpecification", "product-specification-fiber-100", "Fiber 100 Spec"),
                relatedParty=[_party("customer", "party-1001", "Ava Stone")],
                productCharacteristic=[
                    _characteristic("bandwidth", "100 Mbps"),
                    _characteristic("accessTechnology", "FTTH"),
                ],
                realizingService=[_ref("Service", "service-fiber-1001", "Fiber Access Service")],
                note=[_note("Provisioning Bot", "Activation completed and ONT synchronized.")],
            ),
            _base_entity(
                "product-tv-1002",
                base_path,
                name="Entertainment TV Add-on",
                description="Suspended premium television add-on linked to a residential account.",
                status="suspended",
                isBundle=False,
                isCustomerVisible=True,
                startDate="2026-04-08T14:30:00Z",
                terminationDate="2026-05-08T14:30:00Z",
                productSerialNumber="STB-200-1002",
                productOffering=_ref("ProductOffering", "product-offering-tv-premium", "Premium TV"),
                productSpecification=_ref("ProductSpecification", "product-specification-tv-premium", "Premium TV Spec"),
                relatedParty=[_party("customer", "party-1002", "Liam Ortiz")],
                productCharacteristic=[
                    _characteristic("channelPack", "Premium"),
                    _characteristic("parentalControl", "enabled"),
                ],
                realizingService=[_ref("Service", "service-tv-1002", "TV Streaming Service")],
                note=[_note("Care Agent", "Product suspended pending payment resolution.")],
            ),
        ]
    }


def ensure_seed_data(store: Any, base_path: str = DEFAULT_API_BASE_PATH) -> None:
    if store.list_documents(resource_collection("product"), limit=1):
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
    now = utc_now()
    status = payload.get("status", metadata["default_status"])
    return {
        **payload,
        "id": entity_id,
        "href": resource_href(resource_name, entity_id, base_path),
        "status": status,
        "creationDate": payload.get("creationDate", now),
        "lastUpdate": now,
        "statusChangeDate": payload.get("statusChangeDate", now),
        "@type": payload.get("@type", metadata["type"]),
    }


def apply_patch(
    resource_name: str,
    existing: dict[str, Any],
    patch: dict[str, Any],
    base_path: str = DEFAULT_API_BASE_PATH,
) -> dict[str, Any]:
    now = utc_now()
    updated = {
        **existing,
        **patch,
        "id": existing["id"],
        "href": resource_href(resource_name, existing["id"], base_path),
        "creationDate": existing.get("creationDate", now),
        "lastUpdate": now,
        "@type": existing.get("@type", resource_type(resource_name)),
    }
    if patch.get("status") and patch.get("status") != existing.get("status"):
        updated["statusChangeDate"] = now
    else:
        updated["statusChangeDate"] = existing.get("statusChangeDate", now)
    return updated
