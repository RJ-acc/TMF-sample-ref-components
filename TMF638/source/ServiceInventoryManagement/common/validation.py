from __future__ import annotations

from typing import Any

from common.services import SERVICE_OPERATING_STATUSES, SERVICE_STATES, resource_names, resource_type

RESOURCE_NAMES = set(resource_names())
LIST_FIELDS = {
    "relatedParty",
    "serviceCharacteristic",
    "serviceRelationship",
    "supportingService",
    "supportingResource",
    "place",
    "note",
}
OBJECT_FIELDS = {"serviceSpecification"}
STRING_FIELDS = {
    "description",
    "name",
    "state",
    "operatingStatus",
    "category",
    "serviceType",
    "serviceDate",
    "startDate",
    "endDate",
    "@type",
    "@baseType",
    "@schemaLocation",
}
BOOLEAN_FIELDS = {"isBundle", "isServiceEnabled", "hasStarted", "isStateful"}


def _validation_result(errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "errorCount": len(errors),
        "warningCount": len(warnings),
    }


def _validate_reference(reference: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(reference, dict):
        errors.append(f"{prefix} must be an object")
        return
    if reference.get("id") is None or not isinstance(reference.get("id"), str):
        errors.append(f"{prefix}.id must be a string")


def _validate_related_party(item: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(item, dict):
        errors.append(f"{prefix} must be an object")
        return
    if item.get("role") is None or not isinstance(item.get("role"), str):
        errors.append(f"{prefix}.role must be a string")

    nested_ref = item.get("partyOrPartyRole")
    has_root_id = isinstance(item.get("id"), str)
    has_nested_id = isinstance(nested_ref, dict) and isinstance(nested_ref.get("id"), str)
    if not has_root_id and not has_nested_id:
        errors.append(f"{prefix}.id or {prefix}.partyOrPartyRole.id must be a string")


def _validate_characteristic(item: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(item, dict):
        errors.append(f"{prefix} must be an object")
        return
    if not isinstance(item.get("name"), str):
        errors.append(f"{prefix}.name must be a string")
    if item.get("value") is None:
        errors.append(f"{prefix}.value is required")


def _validate_note(item: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(item, dict):
        errors.append(f"{prefix} must be an object")
        return
    if item.get("text") is not None and not isinstance(item.get("text"), str):
        errors.append(f"{prefix}.text must be a string when provided")


def _validate_list(field_name: str, value: Any, errors: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        errors.append(f"{field_name} must be a list when provided")
        return

    for index, item in enumerate(value, start=1):
        prefix = f"{field_name}[{index}]"
        if field_name == "relatedParty":
            _validate_related_party(item, prefix, errors)
        elif field_name == "serviceCharacteristic":
            _validate_characteristic(item, prefix, errors)
        elif field_name == "note":
            _validate_note(item, prefix, errors)
        elif not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")


def _validate_common(resource_name: str, payload: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    for field_name in STRING_FIELDS:
        value = payload.get(field_name)
        if value is not None and not isinstance(value, str):
            errors.append(f"{field_name} must be a string when provided")

    for field_name in BOOLEAN_FIELDS:
        value = payload.get(field_name)
        if value is not None and not isinstance(value, bool):
            errors.append(f"{field_name} must be a boolean when provided")

    state = payload.get("state")
    if state is not None and state not in SERVICE_STATES:
        errors.append(f"state must be one of {sorted(SERVICE_STATES)}")

    operating_status = payload.get("operatingStatus")
    if operating_status is not None and operating_status not in SERVICE_OPERATING_STATUSES:
        errors.append(f"operatingStatus must be one of {sorted(SERVICE_OPERATING_STATUSES)}")

    for field_name in OBJECT_FIELDS:
        value = payload.get(field_name)
        if value is not None:
            _validate_reference(value, field_name, errors)

    for field_name in LIST_FIELDS:
        _validate_list(field_name, payload.get(field_name), errors)

    expected_type = resource_type(resource_name)
    declared_type = payload.get("@type")
    if declared_type is None:
        warnings.append(f"@type is recommended and should usually be '{expected_type}'")
    elif declared_type != expected_type:
        errors.append(f"@type must be '{expected_type}' when provided")

    if payload.get("serviceSpecification") is None:
        warnings.append("serviceSpecification is recommended")
    if payload.get("serviceCharacteristic") is None:
        warnings.append("serviceCharacteristic is recommended")


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

    if not payload.get("name"):
        errors.append("name is required")
    if not payload.get("serviceSpecification"):
        errors.append("serviceSpecification is required")
    if not payload.get("relatedParty"):
        errors.append("relatedParty is required")

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

    for forbidden in ("id", "href", "serviceDate", "lastUpdate"):
        if forbidden in payload:
            errors.append(f"{forbidden} cannot be modified")

    _validate_common(resource_name, payload, errors, warnings)
    return _validation_result(errors, warnings)
