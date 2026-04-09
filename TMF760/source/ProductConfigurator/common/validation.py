from __future__ import annotations

from typing import Any

TASK_STATES = {
    "accepted",
    "terminatedWithError",
    "inProgress",
    "done",
}
STARTER_CHANNELS = {"web", "mobile-app", "retail", "call-center", "partner"}


def _validate_channel(payload: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    channel = payload.get("channel")
    if channel is None:
        warnings.append(f"channel is recommended; starter channels are {sorted(STARTER_CHANNELS)}")
        return
    if not isinstance(channel, dict):
        errors.append("channel must be an object")


def _validate_related_party(payload: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    related_party = payload.get("relatedParty")
    if related_party is None:
        warnings.append("relatedParty is recommended so configuration rules can use customer context")
        return
    if not isinstance(related_party, list):
        errors.append("relatedParty must be a list")
        return
    for index, item in enumerate(related_party, start=1):
        if not isinstance(item, dict):
            errors.append(f"relatedParty[{index}] must be an object")


def _validate_context(payload: dict[str, Any], errors: list[str]) -> None:
    context_entity = payload.get("contextEntity")
    if context_entity is not None and not isinstance(context_entity, dict):
        errors.append("contextEntity must be an object")

    context_characteristic = payload.get("contextCharacteristic")
    if context_characteristic is None:
        return
    if not isinstance(context_characteristic, list):
        errors.append("contextCharacteristic must be a list")
        return
    for index, item in enumerate(context_characteristic, start=1):
        if not isinstance(item, dict):
            errors.append(f"contextCharacteristic[{index}] must be an object")


def _validate_item_list(payload: dict[str, Any], field_name: str, errors: list[str]) -> None:
    items = payload.get(field_name)
    if items is None:
        errors.append(f"{field_name} is required")
        return
    if not isinstance(items, list):
        errors.append(f"{field_name} must be a list")
        return
    if not items:
        errors.append(f"{field_name} must contain at least one item")
        return

    for index, item in enumerate(items, start=1):
        prefix = f"{field_name}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if not item.get("id"):
            errors.append(f"{prefix}.id is required")
        product_configuration = item.get("productConfiguration")
        if not isinstance(product_configuration, dict):
            errors.append(f"{prefix}.productConfiguration must be an object")
            continue
        product_offering = product_configuration.get("productOffering")
        if not isinstance(product_offering, dict):
            errors.append(f"{prefix}.productConfiguration.productOffering must be an object")
            continue
        if not product_offering.get("id"):
            errors.append(f"{prefix}.productConfiguration.productOffering.id is required")


def _validation_result(errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "errorCount": len(errors),
        "warningCount": len(warnings),
    }


def validate_query_product_configuration(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    instant_sync = payload.get("instantSync")
    if instant_sync is not None and not isinstance(instant_sync, bool):
        errors.append("instantSync must be a boolean when provided")

    state = payload.get("state")
    if state and state not in TASK_STATES:
        errors.append(f"state must be one of {sorted(TASK_STATES)}")

    _validate_channel(payload, errors, warnings)
    _validate_related_party(payload, errors, warnings)
    _validate_context(payload, errors)
    _validate_item_list(payload, "requestProductConfigurationItem", errors)

    computed_items = payload.get("computedProductConfigurationItem")
    if computed_items is not None and not isinstance(computed_items, list):
        errors.append("computedProductConfigurationItem must be a list")

    if not payload.get("@type"):
        warnings.append("@type is recommended and should usually be 'QueryProductConfiguration'")

    return _validation_result(errors, warnings)


def validate_check_product_configuration(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    instant_sync = payload.get("instantSync")
    if instant_sync is not None and not isinstance(instant_sync, bool):
        errors.append("instantSync must be a boolean when provided")

    provide_alternatives = payload.get("provideAlternatives")
    if provide_alternatives is not None and not isinstance(provide_alternatives, bool):
        errors.append("provideAlternatives must be a boolean when provided")

    state = payload.get("state")
    if state and state not in TASK_STATES:
        errors.append(f"state must be one of {sorted(TASK_STATES)}")

    _validate_channel(payload, errors, warnings)
    _validate_related_party(payload, errors, warnings)
    _validate_context(payload, errors)
    _validate_item_list(payload, "checkProductConfigurationItem", errors)

    if not payload.get("@type"):
        warnings.append("@type is recommended and should usually be 'CheckProductConfiguration'")

    return _validation_result(errors, warnings)
