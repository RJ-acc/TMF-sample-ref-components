from __future__ import annotations

from typing import Any
from uuid import uuid4

from common.events import utc_now

DEFAULT_API_BASE_PATH = "/tmf-api/partyManagement/v5"
DEFAULT_SEED_TIMESTAMP = "2026-04-09T00:00:00Z"
PARTY_STATES = {
    "initialized",
    "validated",
    "active",
    "inactive",
    "terminated",
}

RESOURCE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "individual": {
        "collection": "individuals",
        "type": "Individual",
        "id_prefix": "individual",
        "default_state": "active",
        "defaults": {
            "partyType": "individual",
        },
    },
    "organization": {
        "collection": "organizations",
        "type": "Organization",
        "id_prefix": "organization",
        "default_state": "active",
        "defaults": {
            "partyType": "organization",
            "isLegalEntity": True,
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
        raise KeyError(f"Unknown TMF632 resource '{resource_name}'") from exc


def resource_type(resource_name: str) -> str:
    return get_resource_definition(resource_name)["type"]


def resource_collection(resource_name: str) -> str:
    return get_resource_definition(resource_name)["collection"]


def resource_href(resource_name: str, entity_id: str, base_path: str = DEFAULT_API_BASE_PATH) -> str:
    return f"{base_path.rstrip('/')}/{resource_name}/{entity_id}"


def _build_name(resource_name: str, fields: dict[str, Any], entity_id: str) -> str:
    if isinstance(fields.get("name"), str) and fields["name"].strip():
        return fields["name"].strip()

    if resource_name == "individual":
        parts = [str(fields.get("givenName", "")).strip(), str(fields.get("familyName", "")).strip()]
        name = " ".join(part for part in parts if part)
        return name or f"Individual {entity_id}"

    for candidate in ("tradingName", "legalName"):
        value = fields.get(candidate)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return f"Organization {entity_id}"


def _base_entity(resource_name: str, entity_id: str, base_path: str, **fields: Any) -> dict[str, Any]:
    metadata = get_resource_definition(resource_name)
    name = _build_name(resource_name, fields, entity_id)
    state = fields.pop("state", metadata["default_state"])
    status = fields.pop("status", state)
    last_update = fields.pop("lastUpdate", DEFAULT_SEED_TIMESTAMP)
    return {
        **metadata["defaults"],
        **fields,
        "id": entity_id,
        "href": resource_href(resource_name, entity_id, base_path),
        "name": name,
        "state": state,
        "status": status,
        "lastUpdate": last_update,
        "@type": metadata["type"],
    }


def _seed_documents(base_path: str) -> dict[str, list[dict[str, Any]]]:
    return {
        "individuals": [
            _base_entity(
                "individual",
                "individual-1001",
                base_path,
                givenName="Ava",
                familyName="Stone",
                birthDate="1990-04-12",
                gender="female",
                description="Primary commercial contact for Northwind Traders.",
                contactMedium=[
                    {
                        "mediumType": "email",
                        "preferred": True,
                        "characteristic": {"emailAddress": "ava.stone@northwind.example"},
                    }
                ],
                externalReference=[{"externalReferenceType": "crm", "name": "crm-ava-1001"}],
            ),
            _base_entity(
                "individual",
                "individual-1002",
                base_path,
                givenName="Liam",
                familyName="Ortiz",
                birthDate="1985-11-03",
                gender="male",
                description="Contoso regional contact for field operations.",
                contactMedium=[
                    {
                        "mediumType": "phone",
                        "preferred": True,
                        "characteristic": {"phoneNumber": "+1-555-0102"},
                    }
                ],
                state="validated",
                status="validated",
            ),
        ],
        "organizations": [
            _base_entity(
                "organization",
                "organization-1001",
                base_path,
                name="Northwind Traders",
                tradingName="Northwind",
                legalName="Northwind Traders LLC",
                organizationType="enterpriseCustomer",
                description="Enterprise customer organization headquartered in Seattle.",
                contactMedium=[
                    {
                        "mediumType": "email",
                        "preferred": True,
                        "characteristic": {"emailAddress": "billing@northwind.example"},
                    }
                ],
            ),
            _base_entity(
                "organization",
                "organization-1002",
                base_path,
                name="Contoso West",
                tradingName="Contoso West",
                legalName="Contoso West Incorporated",
                organizationType="partner",
                description="Regional partner organization for west-coast operations.",
                isHeadOffice=False,
                contactMedium=[
                    {
                        "mediumType": "phone",
                        "preferred": True,
                        "characteristic": {"phoneNumber": "+1-555-0200"},
                    }
                ],
            ),
        ],
    }


def ensure_seed_data(store: Any, base_path: str = DEFAULT_API_BASE_PATH) -> None:
    if store.list_documents(resource_collection("individual"), limit=1):
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
    state = payload.get("state", metadata["default_state"])
    entity = {
        **metadata["defaults"],
        **payload,
        "id": entity_id,
        "href": resource_href(resource_name, entity_id, base_path),
        "state": state,
        "status": payload.get("status", state),
        "lastUpdate": utc_now(),
        "@type": payload.get("@type", metadata["type"]),
    }
    entity["name"] = _build_name(resource_name, entity, entity_id)
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
    if "state" in patch and "status" not in patch:
        updated["status"] = updated["state"]
    updated["name"] = _build_name(resource_name, updated, existing["id"])
    return updated
