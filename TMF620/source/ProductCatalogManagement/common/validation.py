from __future__ import annotations

from typing import Any

from common.catalog import CATALOG_STATES, resource_names, resource_type, supports_patch

RESOURCE_NAMES = set(resource_names())
STRING_FIELDS = {
    "name",
    "description",
    "version",
    "brand",
    "productNumber",
    "state",
    "status",
    "lifecycleStatus",
    "contentType",
    "url",
    "productOfferingType",
    "priceType",
    "recurringChargePeriod",
}
BOOLEAN_FIELDS = {"isRoot", "isBundle", "isSellable"}
OBJECT_FIELDS = {"productSpecification", "productOffering", "price", "validFor"}
LIST_FIELDS = {"category", "productOfferingPrice", "attachment", "note"}


def _validation_result(errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "errorCount": len(errors),
        "warningCount": len(warnings),
    }


def _validate_list(field_name: str, payload: dict[str, Any], errors: list[str]) -> None:
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
    if state is not None and state not in CATALOG_STATES:
        errors.append(f"state must be one of {sorted(CATALOG_STATES)}")

    for field_name in BOOLEAN_FIELDS:
        value = payload.get(field_name)
        if value is not None and not isinstance(value, bool):
            errors.append(f"{field_name} must be a boolean when provided")

    for field_name in OBJECT_FIELDS:
        value = payload.get(field_name)
        if value is not None and not isinstance(value, dict):
            errors.append(f"{field_name} must be an object when provided")

    for field_name in LIST_FIELDS:
        _validate_list(field_name, payload, errors)

    product_catalog = payload.get("productCatalog")
    if product_catalog is not None:
        if resource_name in {"category", "productOffering"}:
            if not isinstance(product_catalog, dict):
                errors.append("productCatalog must be an object when provided")
        elif resource_name == "productSpecification":
            if not isinstance(product_catalog, list):
                errors.append("productCatalog must be a list when provided")
            else:
                for index, item in enumerate(product_catalog, start=1):
                    if not isinstance(item, dict):
                        errors.append(f"productCatalog[{index}] must be an object")
        else:
            errors.append("productCatalog is not supported for this resource")

    if resource_name in {"productCatalog", "category", "productOffering", "productOfferingPrice", "productSpecification"}:
        if payload.get("name") is None:
            warnings.append("name is recommended")

    if resource_name == "productOffering" and payload.get("productSpecification") is None:
        warnings.append("productSpecification is recommended for productOffering")
    if resource_name == "productOfferingPrice" and payload.get("price") is None:
        warnings.append("price is recommended for productOfferingPrice")
    if resource_name in {"importJob", "exportJob"} and payload.get("url") is None:
        warnings.append("url is recommended for import and export jobs")

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

    if not supports_patch(resource_name):
        errors.append(f"resource '{resource_name}' does not support patch")
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
