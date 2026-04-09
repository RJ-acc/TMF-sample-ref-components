from __future__ import annotations

from typing import Any
from uuid import uuid4

from common.events import utc_now

DEFAULT_API_BASE_PATH = "/tmf-api/partyInteractionManagement/v5"
DEFAULT_SEED_TIMESTAMP = "2026-04-09T00:00:00Z"
INTERACTION_STATUSES = {"opened", "inProgress", "completed", "cancelled"}

RESOURCE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "partyInteraction": {
        "collection": "party_interactions",
        "type": "PartyInteraction",
        "id_prefix": "party-interaction",
        "default_status": "opened",
    }
}

RESOURCE_ORDER = ("partyInteraction",)
LISTENER_EVENT_SUFFIXES = (
    "AttributeValueChangeEvent",
    "CreateEvent",
    "DeleteEvent",
    "StatusChangeEvent",
)


def resource_names() -> tuple[str, ...]:
    return RESOURCE_ORDER


def listener_event_types() -> list[str]:
    return [f"{resource_type(resource_name)}{suffix}" for resource_name in RESOURCE_ORDER for suffix in LISTENER_EVENT_SUFFIXES]


def get_resource_definition(resource_name: str) -> dict[str, Any]:
    try:
        return RESOURCE_DEFINITIONS[resource_name]
    except KeyError as exc:
        raise KeyError(f"Unknown TMF683 resource '{resource_name}'") from exc


def resource_type(resource_name: str) -> str:
    return get_resource_definition(resource_name)["type"]


def resource_collection(resource_name: str) -> str:
    return get_resource_definition(resource_name)["collection"]


def resource_href(resource_name: str, entity_id: str, base_path: str = DEFAULT_API_BASE_PATH) -> str:
    return f"{base_path.rstrip('/')}/{resource_name}/{entity_id}"


def _channel(channel_id: str, channel_name: str, role: str) -> dict[str, Any]:
    return {
        "@type": "RelatedChannel",
        "role": role,
        "channel": {
            "@type": "ChannelRef",
            "id": channel_id,
            "name": channel_name,
            "@referredType": "Channel",
        },
    }


def _party(role: str, party_id: str, party_name: str, referred_type: str = "Individual") -> dict[str, Any]:
    return {
        "@type": "RelatedPartyOrPartyRole",
        "role": role,
        "partyOrPartyRole": {
            "@type": "PartyRef",
            "id": party_id,
            "name": party_name,
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


def _base_entity(entity_id: str, base_path: str, **fields: Any) -> dict[str, Any]:
    metadata = get_resource_definition("partyInteraction")
    status = fields.pop("status", metadata["default_status"])
    creation_date = fields.pop("creationDate", DEFAULT_SEED_TIMESTAMP)
    last_update = fields.pop("lastUpdate", creation_date)
    status_change_date = fields.pop("statusChangeDate", last_update)
    return {
        **fields,
        "id": entity_id,
        "href": resource_href("partyInteraction", entity_id, base_path),
        "status": status,
        "creationDate": creation_date,
        "lastUpdate": last_update,
        "statusChangeDate": status_change_date,
        "@type": "PartyInteraction",
    }


def _seed_documents(base_path: str) -> dict[str, list[dict[str, Any]]]:
    return {
        "party_interactions": [
            _base_entity(
                "party-interaction-1001",
                base_path,
                direction="inbound",
                reason="Customer requested order delivery status",
                interactionDate={"startDateTime": "2026-04-07T09:00:00Z", "endDateTime": "2026-04-07T09:20:00Z"},
                description="Customer contacted support through the web portal to confirm expected delivery timing.",
                status="completed",
                relatedChannel=[_channel("web-portal", "Web Portal", "contactChannel")],
                relatedParty=[_party("customer", "party-1001", "Ava Stone")],
                note=[_note("Agent Lee", "Provided latest courier milestone and promised email follow-up.")],
                externalIdentifier=[
                    {
                        "@type": "ExternalIdentifier",
                        "owner": "crm",
                        "externalIdentifierType": "case",
                        "id": "crm-case-1001",
                    }
                ],
            ),
            _base_entity(
                "party-interaction-1002",
                base_path,
                direction="outbound",
                reason="Proactive outage notification",
                interactionDate={"startDateTime": "2026-04-08T14:30:00Z", "endDateTime": "2026-04-08T14:35:00Z"},
                description="Operations team notified the customer about a planned maintenance window via mobile app messaging.",
                status="inProgress",
                relatedChannel=[_channel("mobile-app", "Mobile App", "notificationChannel")],
                relatedParty=[_party("customer", "party-1002", "Liam Ortiz")],
                note=[_note("Ops Bot", "Customer has not yet acknowledged the notification.")],
            ),
        ]
    }


def ensure_seed_data(store: Any, base_path: str = DEFAULT_API_BASE_PATH) -> None:
    if store.list_documents(resource_collection("partyInteraction"), limit=1):
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
