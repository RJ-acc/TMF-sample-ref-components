from __future__ import annotations

from typing import Any

TASK_STATES = {
    "accepted",
    "terminatedWithError",
    "inProgress",
    "done",
}

CUSTOMER_BILL_STATES = {
    "new",
    "issued",
    "delivered",
    "settled",
    "partiallyPaid",
    "cancelled",
}

STARTER_CHANNELS = {"web", "mobile-app", "retail", "call-center", "partner"}


def _validation_result(errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "errorCount": len(errors),
        "warningCount": len(warnings),
    }


def _validate_channel(payload: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    channel = payload.get("channel")
    if channel is None:
        warnings.append(f"channel is recommended; starter channels are {sorted(STARTER_CHANNELS)}")
        return
    if not isinstance(channel, dict):
        errors.append("channel must be an object")
        return
    if channel.get("id") is None and channel.get("name") is None:
        warnings.append("channel should contain at least an id or a name")


def _validate_related_party(payload: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    related_party = payload.get("relatedParty")
    if related_party is None:
        warnings.append("relatedParty is recommended so the generated bill can be linked to a customer")
        return
    if not isinstance(related_party, list):
        errors.append("relatedParty must be a list")
        return
    for index, item in enumerate(related_party, start=1):
        if not isinstance(item, dict):
            errors.append(f"relatedParty[{index}] must be an object")


def _validate_ref_object(
    payload: dict[str, Any],
    field_name: str,
    errors: list[str],
    *,
    required: bool = False,
) -> None:
    value = payload.get(field_name)
    if value is None:
        if required:
            errors.append(f"{field_name} is required")
        return
    if not isinstance(value, dict):
        errors.append(f"{field_name} must be an object")
        return
    if not value.get("id"):
        errors.append(f"{field_name}.id is required")


def validate_customer_bill_on_demand(payload: dict[str, Any]) -> dict[str, Any]:
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
    _validate_ref_object(payload, "billingAccount", errors, required=True)
    _validate_ref_object(payload, "billCycle", errors)

    bill_date = payload.get("billDate")
    if bill_date is not None and not isinstance(bill_date, str):
        errors.append("billDate must be a string when provided")

    if not payload.get("@type"):
        warnings.append("@type is recommended and should usually be 'CustomerBillOnDemand'")

    return _validation_result(errors, warnings)


def validate_customer_bill_patch(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    allowed_fields = {
        "state",
        "paymentDueDate",
        "remainingAmount",
        "amountDue",
        "note",
        "statusReason",
        "@type",
    }

    for key in payload:
        if key not in allowed_fields:
            errors.append(f"{key} is not patchable in this reference implementation")

    state = payload.get("state")
    if state is not None and state not in CUSTOMER_BILL_STATES:
        errors.append(f"state must be one of {sorted(CUSTOMER_BILL_STATES)}")

    if "note" in payload and not isinstance(payload["note"], list):
        errors.append("note must be a list when provided")

    for money_field in ("remainingAmount", "amountDue"):
        value = payload.get(money_field)
        if value is None:
            continue
        if not isinstance(value, dict):
            errors.append(f"{money_field} must be an object")
            continue
        if value.get("value") is None:
            errors.append(f"{money_field}.value is required")
        if value.get("unit") is None:
            warnings.append(f"{money_field}.unit is recommended")

    return _validation_result(errors, warnings)
