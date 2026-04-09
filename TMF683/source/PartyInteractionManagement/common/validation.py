from __future__ import annotations

from typing import Any

from common.interactions import INTERACTION_STATUSES, resource_names, resource_type

RESOURCE_NAMES = set(resource_names())
LIST_FIELDS = {
    "relatedChannel",
    "relatedParty",
    "attachment",
    "note",
    "interactionItem",
    "interactionRelationship",
    "externalIdentifier",
}
OBJECT_FIELDS = {"interactionDate"}
STRING_FIELDS = {"description", "direction", "reason", "status", "@type", "@baseType", "@schemaLocation"}


def _validation_result(errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "errorCount": len(errors),
        "warningCount": len(warnings),
    }


def _validate_channel(channel: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(channel, dict):
        errors.append(f"{prefix} must be an object")
        return
    role = channel.get("role")
    if role is None or not isinstance(role, str):
        errors.append(f"{prefix}.role must be a string")
    channel_ref = channel.get("channel")
    if not isinstance(channel_ref, dict):
        errors.append(f"{prefix}.channel must be an object")
        return
    if not isinstance(channel_ref.get("id"), str):
        errors.append(f"{prefix}.channel.id must be a string")


def _validate_note(note: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(note, dict):
        errors.append(f"{prefix} must be an object")
        return
    text = note.get("text")
    if text is not None and not isinstance(text, str):
        errors.append(f"{prefix}.text must be a string when provided")


def _validate_relationship(relationship: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(relationship, dict):
        errors.append(f"{prefix} must be an object")
        return
    relationship_id = relationship.get("id")
    if relationship_id is None or not isinstance(relationship_id, str):
        errors.append(f"{prefix}.id must be a string")
    relationship_type = relationship.get("relationshipType")
    if relationship_type is not None and not isinstance(relationship_type, str):
        errors.append(f"{prefix}.relationshipType must be a string when provided")


def _validate_external_identifier(identifier: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(identifier, dict):
        errors.append(f"{prefix} must be an object")
        return
    if identifier.get("id") is not None and not isinstance(identifier.get("id"), str):
        errors.append(f"{prefix}.id must be a string when provided")


def _validate_list(field_name: str, value: Any, errors: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        errors.append(f"{field_name} must be a list when provided")
        return
    for index, item in enumerate(value, start=1):
        prefix = f"{field_name}[{index}]"
        if field_name == "relatedChannel":
            _validate_channel(item, prefix, errors)
        elif field_name == "note":
            _validate_note(item, prefix, errors)
        elif field_name == "interactionRelationship":
            _validate_relationship(item, prefix, errors)
        elif field_name == "externalIdentifier":
            _validate_external_identifier(item, prefix, errors)
        elif not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")


def _validate_common(resource_name: str, payload: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    for field_name in STRING_FIELDS:
        value = payload.get(field_name)
        if value is not None and not isinstance(value, str):
            errors.append(f"{field_name} must be a string when provided")

    status = payload.get("status")
    if status is not None and status not in INTERACTION_STATUSES:
        errors.append(f"status must be one of {sorted(INTERACTION_STATUSES)}")

    for field_name in OBJECT_FIELDS:
        value = payload.get(field_name)
        if value is not None and not isinstance(value, dict):
            errors.append(f"{field_name} must be an object when provided")

    for field_name in LIST_FIELDS:
        _validate_list(field_name, payload.get(field_name), errors)

    expected_type = resource_type(resource_name)
    declared_type = payload.get("@type")
    if declared_type is None:
        warnings.append(f"@type is recommended and should usually be '{expected_type}'")
    elif declared_type != expected_type:
        errors.append(f"@type must be '{expected_type}' when provided")

    if payload.get("relatedParty") is None:
        warnings.append("relatedParty is recommended")
    if payload.get("interactionDate") is None:
        warnings.append("interactionDate is recommended")


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

    if not payload.get("direction"):
        errors.append("direction is required")
    if not payload.get("reason"):
        errors.append("reason is required")
    if not payload.get("relatedChannel"):
        errors.append("relatedChannel is required")

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

    for forbidden in ("id", "href", "creationDate", "statusChangeDate", "lastUpdate"):
        if forbidden in payload:
            errors.append(f"{forbidden} cannot be modified")

    _validate_common(resource_name, payload, errors, warnings)
    return _validation_result(errors, warnings)
