from __future__ import annotations

from typing import Any

from common.tickets import (
    TROUBLE_TICKET_SPECIFICATION_STATUSES,
    TROUBLE_TICKET_STATUSES,
    resource_names,
    resource_status_field,
    resource_type,
)

RESOURCE_NAMES = set(resource_names())
COMMON_STRING_FIELDS = {"@type", "@baseType", "@schemaLocation"}
RESOURCE_STRING_FIELDS = {
    "troubleTicket": {
        "description",
        "expectedResolutionDate",
        "externalId",
        "name",
        "priority",
        "requestedResolutionDate",
        "resolutionDate",
        "severity",
        "status",
        "ticketType",
    },
    "troubleTicketSpecification": {
        "description",
        "lifecycleStatus",
        "name",
        "version",
    },
}
RESOURCE_OBJECT_FIELDS = {
    "troubleTicket": {"statusChange"},
    "troubleTicketSpecification": {"validFor"},
}
RESOURCE_LIST_FIELDS = {
    "troubleTicket": {"attachment", "characteristic", "note", "relatedEntity", "relatedParty", "ticketRelationship"},
    "troubleTicketSpecification": {"attachment", "characteristic", "relatedEntity", "relatedParty"},
}


def _validation_result(errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "errorCount": len(errors),
        "warningCount": len(warnings),
    }


def _validate_note(note: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(note, dict):
        errors.append(f"{prefix} must be an object")
        return
    if note.get("text") is not None and not isinstance(note.get("text"), str):
        errors.append(f"{prefix}.text must be a string when provided")


def _validate_related_party(item: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(item, dict):
        errors.append(f"{prefix} must be an object")
        return
    role = item.get("role")
    if role is not None and not isinstance(role, str):
        errors.append(f"{prefix}.role must be a string when provided")
    party_ref = item.get("partyOrPartyRole")
    if party_ref is not None:
        if not isinstance(party_ref, dict):
            errors.append(f"{prefix}.partyOrPartyRole must be an object")
        elif party_ref.get("id") is not None and not isinstance(party_ref.get("id"), str):
            errors.append(f"{prefix}.partyOrPartyRole.id must be a string when provided")


def _validate_related_entity(item: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(item, dict):
        errors.append(f"{prefix} must be an object")
        return
    role = item.get("role")
    if role is not None and not isinstance(role, str):
        errors.append(f"{prefix}.role must be a string when provided")
    entity = item.get("entity")
    if entity is not None:
        if not isinstance(entity, dict):
            errors.append(f"{prefix}.entity must be an object")
        elif entity.get("id") is not None and not isinstance(entity.get("id"), str):
            errors.append(f"{prefix}.entity.id must be a string when provided")


def _validate_status_change(value: Any, errors: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        errors.append("statusChange must be an object when provided")
        return
    for field_name in ("status", "changeDate", "changeReason"):
        field_value = value.get(field_name)
        if field_value is not None and not isinstance(field_value, str):
            errors.append(f"statusChange.{field_name} must be a string when provided")


def _validate_list(field_name: str, value: Any, errors: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        errors.append(f"{field_name} must be a list when provided")
        return
    for index, item in enumerate(value, start=1):
        prefix = f"{field_name}[{index}]"
        if field_name == "note":
            _validate_note(item, prefix, errors)
        elif field_name == "relatedParty":
            _validate_related_party(item, prefix, errors)
        elif field_name == "relatedEntity":
            _validate_related_entity(item, prefix, errors)
        elif not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")


def _validate_common(resource_name: str, payload: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    for field_name in COMMON_STRING_FIELDS | RESOURCE_STRING_FIELDS[resource_name]:
        value = payload.get(field_name)
        if value is not None and not isinstance(value, str):
            errors.append(f"{field_name} must be a string when provided")

    status_field = resource_status_field(resource_name)
    status_value = payload.get(status_field)
    if resource_name == "troubleTicket" and status_value is not None and status_value not in TROUBLE_TICKET_STATUSES:
        errors.append(f"status must be one of {sorted(TROUBLE_TICKET_STATUSES)}")
    if (
        resource_name == "troubleTicketSpecification"
        and status_value is not None
        and status_value not in TROUBLE_TICKET_SPECIFICATION_STATUSES
    ):
        errors.append(f"lifecycleStatus must be one of {sorted(TROUBLE_TICKET_SPECIFICATION_STATUSES)}")

    for field_name in RESOURCE_OBJECT_FIELDS[resource_name]:
        value = payload.get(field_name)
        if value is not None and not isinstance(value, dict):
            errors.append(f"{field_name} must be an object when provided")

    for field_name in RESOURCE_LIST_FIELDS[resource_name]:
        _validate_list(field_name, payload.get(field_name), errors)

    if resource_name == "troubleTicket":
        _validate_status_change(payload.get("statusChange"), errors)

    expected_type = resource_type(resource_name)
    declared_type = payload.get("@type")
    if declared_type is None:
        warnings.append(f"@type is recommended and should usually be '{expected_type}'")
    elif declared_type != expected_type:
        errors.append(f"@type must be '{expected_type}' when provided")

    if resource_name == "troubleTicket":
        if payload.get("relatedParty") is None:
            warnings.append("relatedParty is recommended")
        if payload.get("ticketType") is None:
            warnings.append("ticketType is recommended")
    else:
        if payload.get("version") is None:
            warnings.append("version is recommended")


def validate_create_payload(resource_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if resource_name not in RESOURCE_NAMES:
        errors.append(f"resource '{resource_name}' is not supported")
        return _validation_result(errors, warnings)

    if not isinstance(payload, dict):
        errors.append("payload must be an object")
        return _validation_result(errors, warnings)

    entity_id = payload.get("id")
    if entity_id is not None and not isinstance(entity_id, str):
        errors.append("id must be a string when provided")

    if resource_name == "troubleTicket":
        if not payload.get("description"):
            errors.append("description is required")
        if not payload.get("severity"):
            errors.append("severity is required")
    else:
        if not payload.get("name"):
            errors.append("name is required")
        if not payload.get("description"):
            errors.append("description is required")

    _validate_common(resource_name, payload, errors, warnings)
    return _validation_result(errors, warnings)


def validate_patch_payload(resource_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if resource_name not in RESOURCE_NAMES:
        errors.append(f"resource '{resource_name}' is not supported")
        return _validation_result(errors, warnings)

    if not isinstance(payload, dict):
        errors.append("payload must be an object")
        return _validation_result(errors, warnings)

    if not payload:
        errors.append("patch payload must not be empty")
        return _validation_result(errors, warnings)

    for forbidden in ("id", "href", "creationDate", "lastUpdate"):
        if forbidden in payload:
            errors.append(f"{forbidden} cannot be modified")

    _validate_common(resource_name, payload, errors, warnings)
    return _validation_result(errors, warnings)
