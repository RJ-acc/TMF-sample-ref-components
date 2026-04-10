from __future__ import annotations

from typing import Any
from uuid import uuid4

from common.events import utc_now

DEFAULT_API_BASE_PATH = "/tmf-api/troubleTicket/v5"
DEFAULT_SEED_TIMESTAMP = "2026-04-09T00:00:00Z"
TROUBLE_TICKET_STATUSES = {
    "acknowledged",
    "cancelled",
    "closed",
    "held",
    "inProgress",
    "pending",
    "rejected",
    "resolved",
}
TROUBLE_TICKET_SPECIFICATION_STATUSES = {
    "active",
    "deprecated",
    "draft",
    "inactive",
    "launched",
    "obsolete",
    "retired",
}

RESOURCE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "troubleTicket": {
        "collection": "trouble_tickets",
        "type": "TroubleTicket",
        "id_prefix": "tt",
        "status_field": "status",
        "default_status": "acknowledged",
        "event_suffixes": (
            "AttributeValueChangeEvent",
            "CreateEvent",
            "DeleteEvent",
            "InformationRequiredEvent",
            "ResolvedEvent",
            "StatusChangeEvent",
        ),
    },
    "troubleTicketSpecification": {
        "collection": "trouble_ticket_specifications",
        "type": "TroubleTicketSpecification",
        "id_prefix": "tts",
        "status_field": "lifecycleStatus",
        "default_status": "active",
        "event_suffixes": (
            "AttributeValueChangeEvent",
            "CreateEvent",
            "DeleteEvent",
            "StatusChangeEvent",
        ),
    },
}

RESOURCE_ORDER = ("troubleTicket", "troubleTicketSpecification")


def resource_names() -> tuple[str, ...]:
    return RESOURCE_ORDER


def get_resource_definition(resource_name: str) -> dict[str, Any]:
    try:
        return RESOURCE_DEFINITIONS[resource_name]
    except KeyError as exc:
        raise KeyError(f"Unknown TMF621 resource '{resource_name}'") from exc


def resource_type(resource_name: str) -> str:
    return get_resource_definition(resource_name)["type"]


def resource_collection(resource_name: str) -> str:
    return get_resource_definition(resource_name)["collection"]


def resource_status_field(resource_name: str) -> str:
    return get_resource_definition(resource_name)["status_field"]


def listener_event_suffixes(resource_name: str) -> tuple[str, ...]:
    return get_resource_definition(resource_name)["event_suffixes"]


def listener_event_types() -> list[str]:
    return [
        f"{resource_type(resource_name)}{suffix}"
        for resource_name in RESOURCE_ORDER
        for suffix in listener_event_suffixes(resource_name)
    ]


def resource_href(resource_name: str, entity_id: str, base_path: str = DEFAULT_API_BASE_PATH) -> str:
    return f"{base_path.rstrip('/')}/{resource_name}/{entity_id}"


def _party(role: str, party_id: str, party_name: str, referred_type: str = "Individual") -> dict[str, Any]:
    return {
        "@type": "RelatedParty",
        "role": role,
        "partyOrPartyRole": {
            "@type": "PartyRef",
            "id": party_id,
            "name": party_name,
            "@referredType": referred_type,
        },
    }


def _entity_ref(role: str, entity_id: str, entity_name: str, referred_type: str) -> dict[str, Any]:
    return {
        "@type": "EntityRef",
        "role": role,
        "entity": {
            "@type": "EntityRef",
            "id": entity_id,
            "name": entity_name,
            "@referredType": referred_type,
        },
    }


def _note(author: str, text: str) -> dict[str, Any]:
    return {
        "@type": "Note",
        "author": author,
        "date": DEFAULT_SEED_TIMESTAMP,
        "text": text,
    }


def _status_change(status: str, change_date: str, reason: str) -> dict[str, Any]:
    return {
        "@type": "StatusChange",
        "status": status,
        "changeDate": change_date,
        "changeReason": reason,
    }


def _base_entity(resource_name: str, entity_id: str, base_path: str, **fields: Any) -> dict[str, Any]:
    metadata = get_resource_definition(resource_name)
    status_field = metadata["status_field"]
    status_value = fields.pop(status_field, metadata["default_status"])
    last_update = fields.pop("lastUpdate", DEFAULT_SEED_TIMESTAMP)

    entity = {
        **fields,
        "id": entity_id,
        "href": resource_href(resource_name, entity_id, base_path),
        status_field: status_value,
        "lastUpdate": last_update,
        "@type": metadata["type"],
    }

    if resource_name == "troubleTicket":
        creation_date = fields.get("creationDate", DEFAULT_SEED_TIMESTAMP)
        entity["creationDate"] = creation_date
        entity["statusChange"] = fields.get(
            "statusChange",
            _status_change(status_value, last_update, "Ticket created"),
        )
    else:
        entity["version"] = fields.get("version", "1.0")

    return entity


def _seed_documents(base_path: str) -> dict[str, list[dict[str, Any]]]:
    return {
        "trouble_tickets": [
            _base_entity(
                "troubleTicket",
                "tt-1001",
                base_path,
                name="Broadband outage in district 14",
                description="Customer reported a complete loss of broadband connectivity after a cabinet power event.",
                severity="major",
                priority="high",
                ticketType="incident",
                status="inProgress",
                creationDate="2026-04-07T08:30:00Z",
                lastUpdate="2026-04-08T11:15:00Z",
                expectedResolutionDate="2026-04-09T18:00:00Z",
                relatedEntity=[_entity_ref("service", "svc-1001", "Residential Fiber 500", "Service")],
                relatedParty=[_party("originator", "party-1001", "Ava Stone")],
                note=[_note("Agent Lee", "Dispatch created and network team confirmed power restoration in progress.")],
                statusChange=_status_change("inProgress", "2026-04-08T11:15:00Z", "Dispatch assigned to field operations"),
            ),
            _base_entity(
                "troubleTicket",
                "tt-1002",
                base_path,
                name="Incorrect roaming charge",
                description="Customer disputed a roaming charge that was applied after a failed bundle activation.",
                severity="minor",
                priority="medium",
                ticketType="billing",
                status="resolved",
                creationDate="2026-04-06T16:20:00Z",
                lastUpdate="2026-04-08T09:05:00Z",
                resolutionDate="2026-04-08T09:05:00Z",
                relatedEntity=[_entity_ref("customerBill", "bill-1004", "March 2026 Invoice", "CustomerBill")],
                relatedParty=[_party("originator", "party-1002", "Liam Ortiz")],
                note=[_note("Agent Noor", "Charge reversed after catalog mismatch was confirmed.")],
                statusChange=_status_change("resolved", "2026-04-08T09:05:00Z", "Billing adjustment applied"),
            ),
        ],
        "trouble_ticket_specifications": [
            _base_entity(
                "troubleTicketSpecification",
                "tts-1001",
                base_path,
                name="Service outage trouble ticket",
                description="Specification used when customer-impacting fixed or mobile service outages are reported.",
                version="1.2",
                lifecycleStatus="active",
                relatedEntity=[_entity_ref("productSpecification", "ps-2001", "Fiber Access Service", "ProductSpecification")],
            ),
            _base_entity(
                "troubleTicketSpecification",
                "tts-1002",
                base_path,
                name="Billing dispute trouble ticket",
                description="Specification used for invoice corrections, disputed charges, and credit requests.",
                version="1.0",
                lifecycleStatus="draft",
                relatedEntity=[_entity_ref("billingAccount", "ba-3001", "Consumer Billing Account", "BillingAccount")],
            ),
        ],
    }


def ensure_seed_data(store: Any, base_path: str = DEFAULT_API_BASE_PATH) -> None:
    has_ticket_data = store.list_documents(resource_collection("troubleTicket"), limit=1)
    has_spec_data = store.list_documents(resource_collection("troubleTicketSpecification"), limit=1)
    if has_ticket_data and has_spec_data:
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
    status_field = metadata["status_field"]
    entity_id = payload.get("id") or f"{metadata['id_prefix']}-{uuid4().hex[:8]}"
    now = utc_now()
    status_value = payload.get(status_field, metadata["default_status"])

    entity = {
        **payload,
        "id": entity_id,
        "href": resource_href(resource_name, entity_id, base_path),
        status_field: status_value,
        "lastUpdate": now,
        "@type": payload.get("@type", metadata["type"]),
    }

    if resource_name == "troubleTicket":
        status_change = payload.get("statusChange")
        if not isinstance(status_change, dict):
            status_change = _status_change(status_value, now, "Ticket created")
        entity["creationDate"] = payload.get("creationDate", now)
        entity["statusChange"] = status_change
        if status_value == "resolved" and not entity.get("resolutionDate"):
            entity["resolutionDate"] = now
    else:
        entity["version"] = payload.get("version", "1.0")

    return entity


def apply_patch(
    resource_name: str,
    existing: dict[str, Any],
    patch: dict[str, Any],
    base_path: str = DEFAULT_API_BASE_PATH,
) -> dict[str, Any]:
    metadata = get_resource_definition(resource_name)
    status_field = metadata["status_field"]
    previous_status = existing.get(status_field, metadata["default_status"])
    next_status = patch.get(status_field, previous_status)
    now = utc_now()

    updated = {
        **existing,
        **patch,
        "id": existing["id"],
        "href": resource_href(resource_name, existing["id"], base_path),
        status_field: next_status,
        "lastUpdate": now,
        "@type": existing.get("@type", metadata["type"]),
    }

    if resource_name == "troubleTicket":
        status_change = patch.get("statusChange")
        if next_status != previous_status:
            reason = None
            if isinstance(status_change, dict):
                reason = status_change.get("changeReason")
            updated["statusChange"] = _status_change(
                next_status,
                now,
                reason or f"Status changed from {previous_status} to {next_status}",
            )
        else:
            updated["statusChange"] = (
                status_change
                if isinstance(status_change, dict)
                else existing.get("statusChange", _status_change(next_status, now, "Ticket updated"))
            )
        updated["creationDate"] = existing.get("creationDate", now)
        if next_status == "resolved" and not updated.get("resolutionDate"):
            updated["resolutionDate"] = now
    else:
        updated["version"] = updated.get("version", existing.get("version", "1.0"))

    return updated
