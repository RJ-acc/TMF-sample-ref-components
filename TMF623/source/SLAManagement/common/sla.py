from __future__ import annotations

from typing import Any
from uuid import uuid4

from common.events import utc_now

DEFAULT_API_BASE_PATH = "/tmf-api/slaManagement/v2"
DEFAULT_SEED_TIMESTAMP = "2026-04-09T00:00:00Z"
SLA_STATES = {"draft", "active", "suspended", "retired"}
SLA_VIOLATION_STATES = {"detected", "acknowledged", "resolved", "cancelled"}
SLA_VIOLATION_SEVERITIES = {"minor", "major", "critical"}

RESOURCE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "sla": {
        "collection": "slas",
        "type": "SLA",
        "id_prefix": "sla",
        "defaults": {"state": "draft"},
    },
    "slaViolation": {
        "collection": "sla_violations",
        "type": "SLAViolation",
        "id_prefix": "sla-violation",
        "defaults": {"state": "detected"},
    },
}

RESOURCE_ORDER = ("sla", "slaViolation")
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
        raise KeyError(f"Unknown TMF623 resource '{resource_name}'") from exc


def resource_type(resource_name: str) -> str:
    return get_resource_definition(resource_name)["type"]


def resource_collection(resource_name: str) -> str:
    return get_resource_definition(resource_name)["collection"]


def resource_href(resource_name: str, entity_id: str, base_path: str = DEFAULT_API_BASE_PATH) -> str:
    return f"{base_path.rstrip('/')}/{resource_name}/{entity_id}"


def _entity_ref(entity_id: str, name: str, referred_type: str) -> dict[str, Any]:
    return {
        "id": entity_id,
        "name": name,
        "@referredType": referred_type,
    }


def _note(author: str, text: str) -> dict[str, Any]:
    return {
        "@type": "Note",
        "author": author,
        "date": DEFAULT_SEED_TIMESTAMP,
        "text": text,
    }


def _sla_seed_documents(base_path: str) -> list[dict[str, Any]]:
    return [
        {
            "id": "sla-1001",
            "href": resource_href("sla", "sla-1001", base_path),
            "name": "Enterprise Internet Gold SLA",
            "description": "Availability and response targets for the enterprise internet gold service.",
            "category": "service-assurance",
            "state": "active",
            "creationDate": DEFAULT_SEED_TIMESTAMP,
            "lastUpdate": DEFAULT_SEED_TIMESTAMP,
            "validFor": {
                "startDateTime": "2026-01-01T00:00:00Z",
                "endDateTime": "2026-12-31T23:59:59Z",
            },
            "relatedEntity": [
                _entity_ref("service-1001", "Enterprise Internet Gold", "Service"),
                _entity_ref("customer-1001", "Northwind Manufacturing", "Customer"),
            ],
            "relatedParty": [
                {
                    "role": "provider",
                    "partyOrPartyRole": _entity_ref("party-role-1001", "Operations Team", "PartyRole"),
                },
                {
                    "role": "consumer",
                    "partyOrPartyRole": _entity_ref("organization-1001", "Northwind Manufacturing", "Organization"),
                },
            ],
            "serviceLevelObjective": [
                {
                    "id": "slo-1001",
                    "name": "Availability",
                    "description": "Monthly availability target measured on the access circuit.",
                    "targetEntity": "service-1001",
                    "targetValue": "99.95",
                    "unit": "percent",
                },
                {
                    "id": "slo-1002",
                    "name": "Restoration Time",
                    "description": "Critical incidents restored within four hours.",
                    "targetEntity": "service-1001",
                    "targetValue": "4",
                    "unit": "hours",
                },
            ],
            "rule": [
                {
                    "name": "Availability threshold",
                    "metricName": "serviceAvailability",
                    "comparison": ">=",
                    "targetValue": "99.95",
                    "unit": "percent",
                },
                {
                    "name": "MTTR threshold",
                    "metricName": "meanTimeToRestore",
                    "comparison": "<=",
                    "targetValue": "4",
                    "unit": "hours",
                },
            ],
            "note": [_note("SLA Office", "Gold enterprise SLA activated for 2026 service term.")],
            "@type": "SLA",
        },
        {
            "id": "sla-1002",
            "href": resource_href("sla", "sla-1002", base_path),
            "name": "Wholesale Backhaul Silver SLA",
            "description": "Wholesale backhaul SLA covering monthly latency and service restoration commitments.",
            "category": "wholesale",
            "state": "suspended",
            "creationDate": DEFAULT_SEED_TIMESTAMP,
            "lastUpdate": DEFAULT_SEED_TIMESTAMP,
            "validFor": {
                "startDateTime": "2026-02-01T00:00:00Z",
                "endDateTime": "2027-01-31T23:59:59Z",
            },
            "relatedEntity": [_entity_ref("service-1002", "Wholesale Backhaul Silver", "Service")],
            "serviceLevelObjective": [
                {
                    "id": "slo-2001",
                    "name": "Latency",
                    "description": "Average latency between hub sites during peak windows.",
                    "targetEntity": "service-1002",
                    "targetValue": "30",
                    "unit": "milliseconds",
                }
            ],
            "rule": [
                {
                    "name": "Latency threshold",
                    "metricName": "averageLatency",
                    "comparison": "<=",
                    "targetValue": "30",
                    "unit": "milliseconds",
                }
            ],
            "note": [_note("Partner Ops", "Temporarily suspended during planned network redesign.")],
            "@type": "SLA",
        },
    ]


def _sla_violation_seed_documents(base_path: str) -> list[dict[str, Any]]:
    return [
        {
            "id": "sla-violation-1001",
            "href": resource_href("slaViolation", "sla-violation-1001", base_path),
            "name": "Availability breach April 2026",
            "description": "Planned maintenance overran and reduced monthly availability below target.",
            "state": "acknowledged",
            "severity": "major",
            "reason": "Availability dropped to 99.82% during an extended maintenance window.",
            "violationDate": "2026-04-06T03:15:00Z",
            "creationDate": DEFAULT_SEED_TIMESTAMP,
            "lastUpdate": DEFAULT_SEED_TIMESTAMP,
            "sla": {
                "id": "sla-1001",
                "href": resource_href("sla", "sla-1001", base_path),
                "name": "Enterprise Internet Gold SLA",
                "@referredType": "SLA",
            },
            "serviceLevelObjective": {
                "id": "slo-1001",
                "name": "Availability",
                "@referredType": "ServiceLevelObjective",
            },
            "relatedEntity": [_entity_ref("service-1001", "Enterprise Internet Gold", "Service")],
            "note": [_note("Service Assurance", "Service credits under review.")],
            "@type": "SLAViolation",
        },
        {
            "id": "sla-violation-1002",
            "href": resource_href("slaViolation", "sla-violation-1002", base_path),
            "name": "Restoration delay April 2026",
            "description": "Field repair took longer than the contracted restoration window.",
            "state": "resolved",
            "severity": "critical",
            "reason": "A third-party fiber cut extended restoration time to six hours.",
            "violationDate": "2026-04-08T11:30:00Z",
            "creationDate": DEFAULT_SEED_TIMESTAMP,
            "lastUpdate": DEFAULT_SEED_TIMESTAMP,
            "sla": {
                "id": "sla-1001",
                "href": resource_href("sla", "sla-1001", base_path),
                "name": "Enterprise Internet Gold SLA",
                "@referredType": "SLA",
            },
            "serviceLevelObjective": {
                "id": "slo-1002",
                "name": "Restoration Time",
                "@referredType": "ServiceLevelObjective",
            },
            "relatedEntity": [_entity_ref("incident-1001", "Critical Fiber Incident", "ServiceProblem")],
            "note": [_note("Field Operations", "Violation resolved after alternate routing activation.")],
            "@type": "SLAViolation",
        },
    ]


def _seed_documents(base_path: str) -> dict[str, list[dict[str, Any]]]:
    return {
        "slas": _sla_seed_documents(base_path),
        "sla_violations": _sla_violation_seed_documents(base_path),
    }


def ensure_seed_data(store: Any, base_path: str = DEFAULT_API_BASE_PATH) -> None:
    if store.list_documents(resource_collection("sla"), limit=1):
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
    entity = {
        **metadata["defaults"],
        **payload,
        "id": entity_id,
        "href": resource_href(resource_name, entity_id, base_path),
        "@type": payload.get("@type", metadata["type"]),
        "creationDate": payload.get("creationDate", now),
        "lastUpdate": now,
    }
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
        "creationDate": existing.get("creationDate") or utc_now(),
        "lastUpdate": utc_now(),
    }
    updated["@type"] = updated.get("@type", resource_type(resource_name))
    return updated


def apply_replace(
    resource_name: str,
    existing: dict[str, Any],
    replacement: dict[str, Any],
    base_path: str = DEFAULT_API_BASE_PATH,
) -> dict[str, Any]:
    metadata = get_resource_definition(resource_name)
    updated = {
        **metadata["defaults"],
        **replacement,
        "id": existing["id"],
        "href": resource_href(resource_name, existing["id"], base_path),
        "@type": replacement.get("@type", metadata["type"]),
        "creationDate": existing.get("creationDate") or utc_now(),
        "lastUpdate": utc_now(),
    }
    return updated
