from __future__ import annotations

from typing import Any

from common.parties import PARTY_STATES, resource_names, resource_type

RESOURCE_NAMES = set(resource_names())
LIST_FIELDS = {
    "contactMedium",
    "externalReference",
    "partyCharacteristic",
    "taxExemptionCertificate",
    "otherName",
    "otherLanguageAbility",
    "individualIdentification",
    "organizationIdentification",
    "note",
}
OBJECT_FIELDS = {"validFor"}
STRING_FIELDS = {
    "name",
    "description",
    "status",
    "state",
    "givenName",
    "familyName",
    "middleName",
    "title",
    "gender",
    "birthDate",
    "tradingName",
    "legalName",
    "organizationType",
}
BOOLEAN_FIELDS = {"isHeadOffice", "isLegalEntity"}


def _validation_result(errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "errorCount": len(errors),
        "warningCount": len(warnings),
    }


def _validate_named_object_list(field_name: str, payload: dict[str, Any], errors: list[str]) -> None:
    value = payload.get(field_name)
    if value is None:
        return
    if not isinstance(value, list):
        errors.append(f"{field_name} must be a list when provided")
        return
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            errors.append(f"{field_name}[{index}] must be an object")


def _validate_common(resource_name: str, payload: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    for field_name in STRING_FIELDS:
        value = payload.get(field_name)
        if value is not None and not isinstance(value, str):
            errors.append(f"{field_name} must be a string when provided")

    state = payload.get("state")
    if state is not None and state not in PARTY_STATES:
        errors.append(f"state must be one of {sorted(PARTY_STATES)}")

    for field_name in BOOLEAN_FIELDS:
        value = payload.get(field_name)
        if value is not None and not isinstance(value, bool):
            errors.append(f"{field_name} must be a boolean when provided")

    for field_name in LIST_FIELDS:
        _validate_named_object_list(field_name, payload, errors)

    for field_name in OBJECT_FIELDS:
        value = payload.get(field_name)
        if value is not None and not isinstance(value, dict):
            errors.append(f"{field_name} must be an object when provided")

    if payload.get("contactMedium") is None:
        warnings.append("contactMedium is recommended")

    if resource_name == "individual":
        if not any(payload.get(field) for field in ("name", "givenName", "familyName")):
            warnings.append("individual should include name, givenName, or familyName")
    elif resource_name == "organization":
        if not any(payload.get(field) for field in ("name", "tradingName", "legalName")):
            warnings.append("organization should include name, tradingName, or legalName")

    expected_type = resource_type(resource_name)
    declared_type = payload.get("@type")
    if declared_type is None:
        warnings.append(f"@type is recommended and should usually be '{expected_type}'")
    elif declared_type != expected_type:
        errors.append(f"@type must be '{expected_type}' when provided")


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

    for forbidden in ("id", "href", "lastUpdate"):
        if forbidden in payload:
            errors.append(f"{forbidden} cannot be modified")

    _validate_common(resource_name, payload, errors, warnings)
    return _validation_result(errors, warnings)
