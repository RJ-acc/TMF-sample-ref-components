from __future__ import annotations

from datetime import datetime
from typing import Any

TASK_STATES = {
    "accepted",
    "terminatedWithError",
    "inProgress",
    "done",
}
RECOMMENDATION_TYPES = {
    "upsell",
    "cross-sell",
    "retention",
    "replacement",
    "next-best-action",
}
STARTER_CHANNELS = {"web", "mobile-app", "retail", "call-center", "partner"}


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


def _validate_reference_list(
    payload: dict[str, Any],
    field_name: str,
    errors: list[str],
    *,
    object_required: bool = False,
) -> None:
    value = payload.get(field_name)
    if value in (None, ""):
        return
    if not isinstance(value, list):
        errors.append(f"{field_name} must be a list")
        return
    for index, item in enumerate(value, start=1):
        prefix = f"{field_name}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if object_required and not item:
            errors.append(f"{prefix} must not be empty")


def validate_query_product_recommendation(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    instant_sync = payload.get("instantSyncRecommendation")
    if instant_sync is not None and not isinstance(instant_sync, bool):
        errors.append("instantSyncRecommendation must be a boolean when provided")

    recommendation_type = payload.get("recommendationType")
    if recommendation_type and recommendation_type not in RECOMMENDATION_TYPES:
        warnings.append(
            f"recommendationType '{recommendation_type}' is not in the starter rule set {sorted(RECOMMENDATION_TYPES)}"
        )

    state = payload.get("state")
    if state and state not in TASK_STATES:
        errors.append(f"state must be one of {sorted(TASK_STATES)}")

    categories = payload.get("category")
    if categories is not None:
        if not isinstance(categories, list):
            errors.append("category must be a list")
        else:
            for index, category in enumerate(categories, start=1):
                if not isinstance(category, dict):
                    errors.append(f"category[{index}] must be an object")

    channels = payload.get("channel")
    if channels is not None:
        if not isinstance(channels, list):
            errors.append("channel must be a list")
        else:
            for index, channel in enumerate(channels, start=1):
                if not isinstance(channel, dict):
                    errors.append(f"channel[{index}] must be an object")

    related_party = payload.get("relatedParty")
    if related_party is not None and not isinstance(related_party, dict):
        errors.append("relatedParty must be an object")
    elif not related_party:
        warnings.append("relatedParty is recommended so the recommendation has customer context")

    _validate_reference_list(payload, "productOrder", errors)
    _validate_reference_list(payload, "productOrderItem", errors)
    _validate_reference_list(payload, "shoppingCart", errors)
    _validate_reference_list(payload, "shoppingCartItem", errors)

    recommendation_items = payload.get("recommendationItem")
    if recommendation_items is not None:
        if not isinstance(recommendation_items, list):
            errors.append("recommendationItem must be a list")
        else:
            for index, item in enumerate(recommendation_items, start=1):
                prefix = f"recommendationItem[{index}]"
                if not isinstance(item, dict):
                    errors.append(f"{prefix} must be an object")
                    continue
                if not item.get("product") and not item.get("productOffering"):
                    errors.append(f"{prefix} must include product or productOffering")

    valid_for = payload.get("validFor") or {}
    if valid_for and not isinstance(valid_for, dict):
        errors.append("validFor must be an object")
    else:
        start_date = _parse_datetime(valid_for.get("startDateTime"), "validFor.startDateTime", errors)
        end_date = _parse_datetime(valid_for.get("endDateTime"), "validFor.endDateTime", errors)
        if start_date and end_date and end_date < start_date:
            errors.append("validFor.endDateTime must be greater than or equal to validFor.startDateTime")

    if not recommendation_type:
        warnings.append("recommendationType is recommended to make ranking intent explicit")

    if not payload.get("channel"):
        warnings.append(f"channel is recommended; starter channels are {sorted(STARTER_CHANNELS)}")

    if not payload.get("@type"):
        warnings.append("@type is recommended and should usually be 'QueryProductRecommendation'")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "errorCount": len(errors),
        "warningCount": len(warnings),
    }
