from __future__ import annotations

from typing import Any

from common.access import ACCESS_STATES, resource_names, resource_type

RESOURCE_NAMES = set(resource_names())
LIST_FIELDS = {
    "permission": {"assetUserRole", "privilege"},
    "userRole": {"entitlement"},
}
OBJECT_FIELDS = {
    "permission": {"granter", "user", "validFor"},
    "userRole": set(),
}
STRING_FIELDS = {"description", "involvementRole", "state", "@baseType", "@schemaLocation", "@type"}
FORBIDDEN_PATCH_FIELDS = {"id", "href", "creationDate", "lastUpdate"}


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
    if not isinstance(value.get("id"), str) or not value["id"].strip():
        errors.append(f"{field_name}.id must be a non-empty string")


def _validate_related_party(field_name: str, value: Any, errors: list[str]) -> None:
    _validate_entity_ref(field_name, value, errors)
    if isinstance(value, dict):
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


def _validate_permission_lists(field_name: str, value: Any, errors: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        errors.append(f"{field_name} must be a list when provided")
        return

    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            errors.append(f"{field_name}[{index}] must be an object")
            continue

        if field_name == "assetUserRole":
            manageable_asset = item.get("manageableAsset")
            user_role = item.get("userRole")
            _validate_entity_ref(f"{field_name}[{index}].manageableAsset", manageable_asset, errors)
            _validate_entity_ref(f"{field_name}[{index}].userRole", user_role, errors)
        elif field_name == "privilege":
            manageable_asset = item.get("manageableAsset")
            _validate_entity_ref(f"{field_name}[{index}].manageableAsset", manageable_asset, errors)
            for nested_name in ("action", "function"):
                nested_value = item.get(nested_name)
                if nested_value is None or not isinstance(nested_value, str):
                    errors.append(f"{field_name}[{index}].{nested_name} must be a string")


def _validate_user_role_lists(field_name: str, value: Any, errors: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        errors.append(f"{field_name} must be a list when provided")
        return

    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            errors.append(f"{field_name}[{index}] must be an object")
            continue
        for nested_name in ("action", "function"):
            nested_value = item.get(nested_name)
            if nested_value is not None and not isinstance(nested_value, str):
                errors.append(f"{field_name}[{index}].{nested_name} must be a string when provided")


def _validate_common(resource_name: str, payload: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    _validate_string_fields(payload, errors)

    state = payload.get("state")
    if state is not None and state not in ACCESS_STATES:
        errors.append(f"state must be one of {sorted(ACCESS_STATES)}")

    for field_name in OBJECT_FIELDS[resource_name]:
        value = payload.get(field_name)
        if value is None:
            continue
        if field_name == "validFor":
            _validate_time_period(value, errors)
        else:
            _validate_related_party(field_name, value, errors)

    for field_name in LIST_FIELDS[resource_name]:
        value = payload.get(field_name)
        if resource_name == "permission":
            _validate_permission_lists(field_name, value, errors)
        else:
            _validate_user_role_lists(field_name, value, errors)

    expected_type = resource_type(resource_name)
    declared_type = payload.get("@type")
    if declared_type is None:
        warnings.append(f"@type is recommended and should usually be '{expected_type}'")
    elif declared_type != expected_type:
        errors.append(f"@type must be '{expected_type}' when provided")

    if resource_name == "permission":
        if payload.get("granter") is None:
            warnings.append("granter is recommended for permission records")
        if not payload.get("privilege"):
            warnings.append("privilege is recommended for permission records")
    else:
        if payload.get("involvementRole") is None:
            warnings.append("involvementRole is recommended for userRole records")


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

    if resource_name == "permission":
        if payload.get("user") is None:
            errors.append("user is required")
        if payload.get("validFor") is None:
            errors.append("validFor is required")
    elif not payload.get("entitlement"):
        errors.append("entitlement is required")

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

    for forbidden in FORBIDDEN_PATCH_FIELDS:
        if forbidden in payload:
            errors.append(f"{forbidden} cannot be modified")

    _validate_common(resource_name, payload, errors, warnings)
    return _validation_result(errors, warnings)
