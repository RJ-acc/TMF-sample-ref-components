from __future__ import annotations

from typing import Any

from common.accounts import ACCOUNT_STATES, resource_names

RESOURCE_NAMES = set(resource_names())
REFERENCE_FIELDS = {"billFormat"}
LIST_FIELDS = {"relatedParty", "contact", "characteristic", "note"}
OBJECT_FIELDS = {"accountBalance"}


def _validation_result(errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "errorCount": len(errors),
        "warningCount": len(warnings),
    }


def _validate_common(payload: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    name = payload.get("name")
    if name is not None and not isinstance(name, str):
        errors.append("name must be a string when provided")
    if name is None:
        warnings.append("name is recommended")

    description = payload.get("description")
    if description is not None and not isinstance(description, str):
        errors.append("description must be a string when provided")

    state = payload.get("state")
    if state is not None and state not in ACCOUNT_STATES:
        errors.append(f"state must be one of {sorted(ACCOUNT_STATES)}")

    status = payload.get("status")
    if status is not None and not isinstance(status, str):
        errors.append("status must be a string when provided")

    for field_name in LIST_FIELDS:
        value = payload.get(field_name)
        if value is not None and not isinstance(value, list):
            errors.append(f"{field_name} must be a list when provided")

    for field_name in OBJECT_FIELDS:
        value = payload.get(field_name)
        if value is not None and not isinstance(value, dict):
            errors.append(f"{field_name} must be an object when provided")

    bill_format = payload.get("billFormat")
    if bill_format is not None:
        if not isinstance(bill_format, dict):
            errors.append("billFormat must be an object when provided")
        elif not bill_format.get("id"):
            errors.append("billFormat.id is required when billFormat is provided")

    if payload.get("relatedParty") is None and payload.get("@type") in {
        "BillingAccount",
        "PartyAccount",
    }:
        warnings.append("relatedParty is recommended for customer-facing account resources")


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

    _validate_common(payload, errors, warnings)

    if resource_name == "billPresentationMedia" and payload.get("billFormat") is None:
        warnings.append("billFormat is recommended for billPresentationMedia resources")

    if resource_name == "billingCycleSpecification":
        frequency = payload.get("frequency")
        if frequency is not None and not isinstance(frequency, str):
            errors.append("frequency must be a string when provided")

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

    for forbidden in ("id", "href", "lastUpdate"):
        if forbidden in payload:
            errors.append(f"{forbidden} cannot be modified")

    _validate_common(payload, errors, warnings)
    return _validation_result(errors, warnings)
