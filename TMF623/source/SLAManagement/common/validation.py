from __future__ import annotations

from typing import Any

from common.sla import (
    SLA_STATES,
    SLA_VIOLATION_SEVERITIES,
    SLA_VIOLATION_STATES,
    resource_names,
    resource_type,
)

RESOURCE_NAMES = set(resource_names())
LIST_FIELDS = {
    "sla": {"relatedEntity", "relatedParty", "rule", "serviceLevelObjective", "note"},
    "slaViolation": {"relatedEntity", "note"},
}
OBJECT_FIELDS = {
    "sla": {"validFor"},
    "slaViolation": {"sla", "serviceLevelObjective"},
}
STRING_FIELDS = {
    "name",
    "description",
    "category",
    "state",
    "severity",
    "reason",
    "violationDate",
    "@baseType",
    "@schemaLocation",
    "@type",
}
FORBIDDEN_MUTATION_FIELDS = {"id", "href", "creationDate", "lastUpdate"}


def _validation_result(errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "errorCount": len(errors),
        "warningCount": len(warnings),
    }


def _validate_string_fields(payload: dict[str, Any], errors: list[str]) -> None:
    for field_name in STRING_FIELDS:
        value = payload.get(field_name)
        if value is not None and not isinstance(value, str):
            errors.append(f"{field_name} must be a string when provided")


def _validate_entity_ref(field_name: str, value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{field_name} must be an object when provided")
        return
    entity_id = value.get("id")
    if entity_id is None or not isinstance(entity_id, str) or not entity_id.strip():
        errors.append(f"{field_name}.id must be a non-empty string")
    referred_type = value.get("@referredType")
    if referred_type is not None and not isinstance(referred_type, str):
        errors.append(f"{field_name}.@referredType must be a string when provided")


def _validate_time_period(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("validFor must be an object when provided")
        return
    for field_name in ("startDateTime", "endDateTime"):
        field_value = value.get(field_name)
        if field_value is not None and not isinstance(field_value, str):
            errors.append(f"validFor.{field_name} must be a string when provided")


def _validate_note(value: Any, field_name: str, index: int, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{field_name}[{index}] must be an object")
        return
    text = value.get("text")
    if text is not None and not isinstance(text, str):
        errors.append(f"{field_name}[{index}].text must be a string when provided")


def _validate_related_party(value: Any, field_name: str, index: int, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{field_name}[{index}] must be an object")
        return
    role = value.get("role")
    if role is not None and not isinstance(role, str):
        errors.append(f"{field_name}[{index}].role must be a string when provided")
    party_ref = value.get("partyOrPartyRole")
    _validate_entity_ref(f"{field_name}[{index}].partyOrPartyRole", party_ref, errors)


def _validate_rule(value: Any, field_name: str, index: int, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{field_name}[{index}] must be an object")
        return
    for nested_name in ("name", "metricName", "comparison", "targetValue"):
        nested_value = value.get(nested_name)
        if nested_value is None or not isinstance(nested_value, str):
            errors.append(f"{field_name}[{index}].{nested_name} must be a string")


def _validate_objective(value: Any, field_name: str, index: int, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{field_name}[{index}] must be an object")
        return
    for nested_name in ("id", "name", "targetValue"):
        nested_value = value.get(nested_name)
        if nested_value is None or not isinstance(nested_value, str):
            errors.append(f"{field_name}[{index}].{nested_name} must be a string")


def _validate_list(resource_name: str, field_name: str, value: Any, errors: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        errors.append(f"{field_name} must be a list when provided")
        return

    for index, item in enumerate(value, start=1):
        if field_name == "note":
            _validate_note(item, field_name, index, errors)
        elif field_name == "relatedParty":
            _validate_related_party(item, field_name, index, errors)
        elif field_name == "rule":
            _validate_rule(item, field_name, index, errors)
        elif field_name == "serviceLevelObjective":
            _validate_objective(item, field_name, index, errors)
        else:
            _validate_entity_ref(f"{field_name}[{index}]", item, errors)


def _validate_common(resource_name: str, payload: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    _validate_string_fields(payload, errors)

    state = payload.get("state")
    if state is not None:
        allowed_states = SLA_STATES if resource_name == "sla" else SLA_VIOLATION_STATES
        if state not in allowed_states:
            errors.append(f"state must be one of {sorted(allowed_states)}")

    if resource_name == "slaViolation":
        severity = payload.get("severity")
        if severity is not None and severity not in SLA_VIOLATION_SEVERITIES:
            errors.append(f"severity must be one of {sorted(SLA_VIOLATION_SEVERITIES)}")

    for field_name in OBJECT_FIELDS[resource_name]:
        value = payload.get(field_name)
        if value is None:
            continue
        if field_name == "validFor":
            _validate_time_period(value, errors)
        else:
            _validate_entity_ref(field_name, value, errors)

    for field_name in LIST_FIELDS[resource_name]:
        _validate_list(resource_name, field_name, payload.get(field_name), errors)

    expected_type = resource_type(resource_name)
    declared_type = payload.get("@type")
    if declared_type is None:
        warnings.append(f"@type is recommended and should usually be '{expected_type}'")
    elif declared_type != expected_type:
        errors.append(f"@type must be '{expected_type}' when provided")

    if resource_name == "sla":
        if payload.get("relatedEntity") is None:
            warnings.append("relatedEntity is recommended for SLA records")
        if payload.get("rule") is None:
            warnings.append("rule is recommended for SLA records")
    else:
        if payload.get("serviceLevelObjective") is None:
            warnings.append("serviceLevelObjective is recommended for SLA violation records")
        if payload.get("violationDate") is None:
            warnings.append("violationDate is recommended for SLA violation records")


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

    if resource_name == "sla":
        if payload.get("name") is None:
            errors.append("name is required")
        if payload.get("validFor") is None:
            errors.append("validFor is required")
        if not payload.get("serviceLevelObjective"):
            errors.append("serviceLevelObjective is required")
    else:
        if payload.get("sla") is None:
            errors.append("sla is required")
        if payload.get("severity") is None:
            errors.append("severity is required")
        if payload.get("reason") is None:
            errors.append("reason is required")

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

    for forbidden in FORBIDDEN_MUTATION_FIELDS:
        if forbidden in payload:
            errors.append(f"{forbidden} cannot be modified")

    _validate_common(resource_name, payload, errors, warnings)
    return _validation_result(errors, warnings)


def validate_replace_payload(resource_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if resource_name not in RESOURCE_NAMES:
        errors.append(f"resource '{resource_name}' is not supported")
        return _validation_result(errors, warnings)

    if not isinstance(payload, dict):
        errors.append("payload must be an object")
        return _validation_result(errors, warnings)

    for forbidden in FORBIDDEN_MUTATION_FIELDS:
        if forbidden in payload:
            errors.append(f"{forbidden} cannot be modified")

    create_result = validate_create_payload(resource_name, payload)
    errors.extend(create_result["errors"])
    warnings.extend(create_result["warnings"])
    return _validation_result(errors, warnings)
