from __future__ import annotations

from typing import Any
from uuid import uuid4

from common.events import utc_now

DEFAULT_API_BASE_PATH = "/tmf-api/serviceInventoryManagement/v5"
DEFAULT_SEED_TIMESTAMP = "2026-04-09T00:00:00Z"
SERVICE_STATES = {
    "feasibilityChecked",
    "designed",
    "reserved",
    "active",
    "inactive",
    "terminated",
}
SERVICE_OPERATING_STATUSES = {
    "pending",
    "configured",
    "starting",
    "running",
    "degraded",
    "failed",
    "limited",
    "stopping",
    "stopped",
    "unknown",
}

RESOURCE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "service": {
        "collection": "services",
        "type": "Service",
        "id_prefix": "service",
        "default_state": "feasibilityChecked",
        "default_operating_status": "pending",
    }
}

RESOURCE_ORDER = ("service",)
LISTENER_EVENT_SUFFIXES = (
    "AttributeValueChangeEvent",
    "CreateEvent",
    "DeleteEvent",
    "OperatingStatusChangeEvent",
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
        raise KeyError(f"Unknown TMF638 resource '{resource_name}'") from exc


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
    metadata = get_resource_definition("service")
    state = fields.pop("state", metadata["default_state"])
    operating_status = fields.pop("operatingStatus", metadata["default_operating_status"])
    service_date = fields.pop("serviceDate", DEFAULT_SEED_TIMESTAMP)
    last_update = fields.pop("lastUpdate", service_date)
    return {
        **fields,
        "id": entity_id,
        "href": resource_href("service", entity_id, base_path),
        "state": state,
        "operatingStatus": operating_status,
        "serviceDate": service_date,
        "lastUpdate": last_update,
        "@type": "Service",
    }


def _seed_documents(base_path: str) -> dict[str, list[dict[str, Any]]]:
    return {
        "services": [
            _base_entity(
                "service-fiber-1001",
                base_path,
                name="Fiber Access Service",
                description="Customer-facing residential fiber access service with 100 Mbps downstream bandwidth.",
                state="active",
                operatingStatus="running",
                isBundle=False,
                isServiceEnabled=True,
                hasStarted=True,
                isStateful=True,
                category="CustomerFacingService",
                serviceType="BroadbandAccess",
                serviceDate="2026-04-07T09:00:00Z",
                startDate="2026-04-07T09:00:00Z",
                serviceSpecification=_ref("ServiceSpecification", "service-spec-fiber-100", "Fiber Access CFS"),
                relatedParty=[_party("customer", "party-1001", "Ava Stone")],
                serviceCharacteristic=[
                    _characteristic("bandwidth", "100 Mbps"),
                    _characteristic("accessTechnology", "FTTH"),
                ],
                supportingService=[_ref("Service", "service-olt-2001", "OLT Aggregation Service")],
                note=[_note("Provisioning Bot", "Activation completed and ONT synchronized.")],
            ),
            _base_entity(
                "service-tv-1002",
                base_path,
                name="Premium TV Service",
                description="Customer-facing IPTV service currently inactive after a scheduled suspension.",
                state="inactive",
                operatingStatus="stopped",
                isBundle=False,
                isServiceEnabled=False,
                hasStarted=True,
                isStateful=True,
                category="CustomerFacingService",
                serviceType="VideoStreaming",
                serviceDate="2026-04-08T14:30:00Z",
                startDate="2026-04-08T14:30:00Z",
                endDate="2026-05-08T14:30:00Z",
                serviceSpecification=_ref("ServiceSpecification", "service-spec-tv-premium", "Premium IPTV CFS"),
                relatedParty=[_party("customer", "party-1002", "Liam Ortiz")],
                serviceCharacteristic=[
                    _characteristic("channelPack", "Premium"),
                    _characteristic("parentalControl", "enabled"),
                ],
                supportingService=[_ref("Service", "service-cdn-3002", "Video Delivery Service")],
                note=[_note("Care Agent", "Service suspended pending payment resolution.")],
            ),
        ]
    }


def ensure_seed_data(store: Any, base_path: str = DEFAULT_API_BASE_PATH) -> None:
    if store.list_documents(resource_collection("service"), limit=1):
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
    state = payload.get("state", metadata["default_state"])
    operating_status = payload.get("operatingStatus", metadata["default_operating_status"])
    return {
        **payload,
        "id": entity_id,
        "href": resource_href(resource_name, entity_id, base_path),
        "state": state,
        "operatingStatus": operating_status,
        "serviceDate": payload.get("serviceDate", now),
        "lastUpdate": now,
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
        "serviceDate": existing.get("serviceDate", now),
        "lastUpdate": now,
        "@type": existing.get("@type", resource_type(resource_name)),
    }
    return updated
