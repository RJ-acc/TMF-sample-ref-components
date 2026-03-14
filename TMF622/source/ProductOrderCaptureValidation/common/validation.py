from __future__ import annotations

from datetime import datetime
from typing import Any

ORDER_STATES = {
    "acknowledged",
    "rejected",
    "pending",
    "held",
    "inProgress",
    "cancelled",
    "completed",
    "failed",
    "partial",
    "assessingCancellation",
    "pendingCancellation",
}

ORDER_ITEM_STATES = {
    "acknowledged",
    "rejected",
    "pending",
    "held",
    "inProgress",
    "cancelled",
    "completed",
    "failed",
    "assessingCancellation",
    "pendingCancellation",
}

ORDER_ACTIONS = {"add", "modify", "delete", "noChange"}
TASK_STATES = {"acknowledged", "terminatedWithError", "inProgress", "done"}


def _parse_datetime(value: Any, field_name: str, errors: list[str]) -> datetime | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        errors.append(f"{field_name} must be an ISO-8601 string")
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{field_name} must be a valid ISO-8601 date-time")
        return None


def validate_product_order(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    order_items = payload.get("productOrderItem")
    if not isinstance(order_items, list) or not order_items:
        errors.append("productOrderItem is required and must contain at least one entry")
    else:
        for index, item in enumerate(order_items, start=1):
            prefix = f"productOrderItem[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            if not item.get("id"):
                errors.append(f"{prefix}.id is required")
            action = item.get("action")
            if action not in ORDER_ACTIONS:
                errors.append(f"{prefix}.action must be one of {sorted(ORDER_ACTIONS)}")
            state = item.get("state")
            if state and state not in ORDER_ITEM_STATES:
                errors.append(f"{prefix}.state must be one of {sorted(ORDER_ITEM_STATES)}")
            if item.get("quantity") is not None:
                try:
                    if int(item.get("quantity")) < 1:
                        errors.append(f"{prefix}.quantity must be greater than zero")
                except (TypeError, ValueError):
                    errors.append(f"{prefix}.quantity must be an integer")

            product_ref = item.get("product")
            offering_ref = item.get("productOffering")
            qualification_item = item.get("productOfferingQualificationItem")
            if not any([product_ref, offering_ref, qualification_item]):
                errors.append(
                    f"{prefix} must reference product, productOffering, or productOfferingQualificationItem"
                )
            elif offering_ref and isinstance(offering_ref, dict) and not offering_ref.get("id"):
                warnings.append(f"{prefix}.productOffering should include an id")

    order_state = payload.get("state")
    if order_state and order_state not in ORDER_STATES:
        errors.append(f"state must be one of {sorted(ORDER_STATES)}")

    requested_start = _parse_datetime(payload.get("requestedStartDate"), "requestedStartDate", errors)
    requested_completion = _parse_datetime(
        payload.get("requestedCompletionDate"), "requestedCompletionDate", errors
    )
    cancellation_date = _parse_datetime(payload.get("cancellationDate"), "cancellationDate", errors)

    if requested_start and requested_completion and requested_completion < requested_start:
        errors.append("requestedCompletionDate must be greater than or equal to requestedStartDate")
    if cancellation_date and requested_start and cancellation_date < requested_start:
        warnings.append("cancellationDate is earlier than requestedStartDate")

    priority = payload.get("priority")
    if priority not in (None, "") and str(priority) not in {"0", "1", "2", "3", "4"}:
        warnings.append("priority is expected to be a value between 0 and 4")

    related_parties = payload.get("relatedParty")
    if not isinstance(related_parties, list) or not related_parties:
        warnings.append("relatedParty is recommended so the order has a clear customer or buyer context")
    else:
        has_customer_context = any(
            isinstance(party, dict) and str(party.get("role", "")).lower() in {"customer", "buyer", "requester"}
            for party in related_parties
        )
        if not has_customer_context:
            warnings.append("relatedParty should normally include a Customer, Buyer, or Requester role")

    if not payload.get("notificationContact"):
        warnings.append("notificationContact is recommended for order progress notifications")

    if not payload.get("@type"):
        warnings.append("@type is recommended and should usually be 'ProductOrder'")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "errorCount": len(errors),
        "warningCount": len(warnings),
    }


def validate_cancel_product_order(
    payload: dict[str, Any],
    product_order_exists: bool | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    product_order = payload.get("productOrder")
    if not isinstance(product_order, dict) or not product_order.get("id"):
        errors.append("productOrder.id is required for a cancellation request")

    if product_order_exists is False:
        errors.append("The referenced product order does not exist")

    state = payload.get("state")
    if state and state not in TASK_STATES:
        errors.append(f"state must be one of {sorted(TASK_STATES)}")

    _parse_datetime(payload.get("requestedCancellationDate"), "requestedCancellationDate", errors)

    if not payload.get("cancellationReason"):
        warnings.append("cancellationReason is recommended for downstream handling and audit")

    if not payload.get("@type"):
        warnings.append("@type is recommended and should usually be 'CancelProductOrder'")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "errorCount": len(errors),
        "warningCount": len(warnings),
    }
