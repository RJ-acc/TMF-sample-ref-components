from __future__ import annotations

from typing import Any

from common.validation import validate_check_product_configuration, validate_query_product_configuration

STARTER_CATALOG = [
    {
        "id": "14305",
        "name": "Mobile Handset",
        "description": "Starter mobile handset offering used for deterministic TMF760 configuration flows.",
        "href": "https://host:port/productCatalogManagement/v5/productOffering/14305",
        "basePrice": 100,
        "currency": "EUR",
        "actions": [
            {"action": "add", "description": "Add new product", "defaultSelected": True},
            {"action": "modify", "description": "Modify existing product", "defaultSelected": False},
        ],
        "terms": [
            {"name": "12 month contract", "defaultSelected": False},
            {"name": "24 month contract", "defaultSelected": False},
        ],
        "characteristics": [
            {
                "id": "77",
                "name": "Color",
                "valueType": "string",
                "minCardinality": 1,
                "maxCardinality": 1,
                "values": [
                    {"value": "Blue", "defaultSelected": True, "priceAdjustment": 0},
                    {"value": "Red", "defaultSelected": False, "priceAdjustment": 10},
                ],
            },
            {
                "id": "78",
                "name": "Storage",
                "valueType": "string",
                "minCardinality": 1,
                "maxCardinality": 1,
                "values": [
                    {"value": "128GB", "defaultSelected": True, "priceAdjustment": 0},
                    {"value": "256GB", "defaultSelected": False, "priceAdjustment": 40},
                ],
            },
        ],
    },
    {
        "id": "fiber-500",
        "name": "Fiber Broadband 500",
        "description": "Starter broadband offering used for deterministic TMF760 configuration flows.",
        "href": "https://host:port/productCatalogManagement/v5/productOffering/fiber-500",
        "basePrice": 59,
        "currency": "EUR",
        "actions": [
            {"action": "add", "description": "Add new product", "defaultSelected": True},
            {"action": "modify", "description": "Change existing product", "defaultSelected": False},
        ],
        "terms": [
            {"name": "Monthly rolling", "defaultSelected": True},
            {"name": "12 month contract", "defaultSelected": False},
        ],
        "characteristics": [
            {
                "id": "91",
                "name": "Router",
                "valueType": "string",
                "minCardinality": 1,
                "maxCardinality": 1,
                "values": [
                    {"value": "Included", "defaultSelected": True, "priceAdjustment": 0},
                    {"value": "Premium Mesh", "defaultSelected": False, "priceAdjustment": 12},
                ],
            }
        ],
    },
]

STARTER_CATALOG_INDEX = {entry["id"]: entry for entry in STARTER_CATALOG}


def _money(amount: int | float, currency: str) -> dict[str, Any]:
    return {"unit": currency, "value": amount, "@type": "Money"}


def _configuration_price(name: str, offering_id: str, offering_name: str, amount: int | float, currency: str) -> dict[str, Any]:
    return {
        "@type": "ConfigurationPrice",
        "name": name,
        "priceType": "oneTimeCharge",
        "productOfferingPrice": {
            "id": f"{offering_id}-price",
            "href": f"https://host:port/productCatalogManagement/v5/productOfferingPrice/{offering_id}-price",
            "name": f"{offering_name} configured price",
            "@referredType": "ProductOfferingPrice",
            "@type": "ProductOfferingPrice",
        },
        "price": {
            "taxRate": 22,
            "@type": "Price",
            "dutyFreeAmount": _money(amount, currency),
            "taxIncludedAmount": _money(round(amount * 1.22, 2), currency),
        },
    }


def _offering_ref(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": entry["id"],
        "href": entry["href"],
        "name": entry["name"],
        "@type": "ProductOfferingRef",
    }


def _state_reason(code: str, label: str) -> dict[str, Any]:
    return {"code": code, "label": label, "@type": "StateReason"}


def _selected_names(entries: list[dict[str, Any]] | None, key: str) -> set[str]:
    selected: set[str] = set()
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue
        if entry.get("isSelected") and entry.get(key):
            selected.add(str(entry[key]))
    return selected


def _selected_characteristic_values(configuration: dict[str, Any] | None) -> dict[str, list[str]]:
    selected: dict[str, list[str]] = {}
    if not isinstance(configuration, dict):
        return selected

    for characteristic in configuration.get("configurationCharacteristic") or []:
        if not isinstance(characteristic, dict):
            continue
        values = []
        for option in characteristic.get("configurationCharacteristicValue") or []:
            if not isinstance(option, dict) or not option.get("isSelected"):
                continue
            characteristic_value = option.get("characteristicValue") or {}
            raw_value = characteristic_value.get("value")
            if raw_value is not None:
                values.append(str(raw_value))
        if values:
            if characteristic.get("id"):
                selected[str(characteristic["id"])] = values
            if characteristic.get("name"):
                selected[str(characteristic["name"]).lower()] = values
    return selected


def _selected_term_names(configuration: dict[str, Any] | None) -> set[str]:
    if not isinstance(configuration, dict):
        return set()
    return _selected_names(configuration.get("configurationTerm"), "name")


def _selected_action_names(configuration: dict[str, Any] | None) -> set[str]:
    if not isinstance(configuration, dict):
        return set()
    return _selected_names(configuration.get("configurationAction"), "action")


def _normalize_product_configuration(
    entry: dict[str, Any],
    requested_configuration: dict[str, Any] | None,
    *,
    allow_defaults: bool,
) -> dict[str, Any]:
    requested_configuration = requested_configuration or {}
    selected_actions = _selected_action_names(requested_configuration)
    selected_terms = _selected_term_names(requested_configuration)
    selected_values = _selected_characteristic_values(requested_configuration)

    configuration_actions = []
    for action in entry["actions"]:
        is_selected = action["action"] in selected_actions
        if not selected_actions and allow_defaults:
            is_selected = action.get("defaultSelected", False)
        configuration_actions.append(
            {
                "@type": "ConfigurationAction",
                "action": action["action"],
                "description": action["description"],
                "isSelected": is_selected,
            }
        )

    configuration_terms = []
    for term in entry["terms"]:
        is_selected = term["name"] in selected_terms
        if not selected_terms and allow_defaults:
            is_selected = term.get("defaultSelected", False)
        configuration_terms.append(
            {
                "@type": "ConfigurationTerm",
                "name": term["name"],
                "isSelectable": True,
                "isSelected": is_selected,
            }
        )

    total_price = entry.get("basePrice", 0)
    configuration_characteristics = []
    for characteristic in entry["characteristics"]:
        selected_for_characteristic = (
            selected_values.get(str(characteristic["id"]))
            or selected_values.get(str(characteristic["name"]).lower())
            or []
        )
        option_documents = []
        for option in characteristic["values"]:
            is_selected = option["value"] in selected_for_characteristic
            if not selected_for_characteristic and allow_defaults:
                is_selected = option.get("defaultSelected", False)
            if is_selected:
                total_price += option.get("priceAdjustment", 0)
            option_documents.append(
                {
                    "@type": "ConfigurationCharacteristicValue",
                    "isSelectable": True,
                    "isSelected": is_selected,
                    "isVisible": True,
                    "characteristicValue": {
                        "name": characteristic["name"],
                        "value": option["value"],
                        "@type": "StringCharacteristic",
                    },
                }
            )

        configuration_characteristics.append(
            {
                "@type": "ConfigurationCharacteristic",
                "id": characteristic["id"],
                "name": characteristic["name"],
                "valueType": characteristic["valueType"],
                "minCardinality": characteristic["minCardinality"],
                "maxCardinality": characteristic["maxCardinality"],
                "isConfigurable": True,
                "isVisible": True,
                "configurationCharacteristicValue": option_documents,
            }
        )

    return {
        "@type": "ProductConfiguration",
        "id": requested_configuration.get("id") or entry["id"],
        "isSelectable": False,
        "isSelected": True,
        "isVisible": True,
        "productOffering": _offering_ref(entry),
        "configurationAction": configuration_actions,
        "configurationTerm": configuration_terms,
        "configurationCharacteristic": configuration_characteristics,
        "configurationPrice": [
            _configuration_price(
                name=f"{entry['name']} configured price",
                offering_id=entry["id"],
                offering_name=entry["name"],
                amount=total_price,
                currency=entry["currency"],
            )
        ],
    }


def _unknown_offering_item(item_id: str, offering_id: str | None, resource_type: str) -> dict[str, Any]:
    return {
        "@type": f"{resource_type}Item",
        "id": item_id,
        "state": "rejected",
        "stateReason": [
            _state_reason(
                "UNKNOWN_PRODUCT_OFFERING",
                f"Product offering '{offering_id or 'missing'}' is not in the starter catalog",
            )
        ],
    }


def _validate_selected_configuration(entry: dict[str, Any], requested_configuration: dict[str, Any]) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = []
    selected_values = _selected_characteristic_values(requested_configuration)
    selected_terms = _selected_term_names(requested_configuration)
    allowed_terms = {term["name"] for term in entry["terms"]}

    for selected_term in selected_terms:
        if selected_term not in allowed_terms:
            reasons.append(_state_reason("INVALID_TERM", f"Configuration term '{selected_term}' is not allowed"))
    if len(selected_terms) > 1:
        reasons.append(_state_reason("TOO_MANY_TERMS", "At most one configuration term can be selected"))

    for characteristic in entry["characteristics"]:
        keys = [str(characteristic["id"]), str(characteristic["name"]).lower()]
        chosen: set[str] = set()
        for key in keys:
            chosen.update(selected_values.get(key, []))
        allowed_values = {option["value"] for option in characteristic["values"]}
        if characteristic["minCardinality"] > 0 and not chosen:
            reasons.append(
                _state_reason(
                    "MISSING_CHARACTERISTIC",
                    f"Configured product is missing characteristic '{characteristic['name']}'",
                )
            )
            continue
        if len(chosen) > characteristic["maxCardinality"]:
            reasons.append(
                _state_reason(
                    "TOO_MANY_VALUES",
                    f"Characteristic '{characteristic['name']}' exceeds max cardinality {characteristic['maxCardinality']}",
                )
            )
        for value in chosen:
            if value not in allowed_values:
                reasons.append(
                    _state_reason(
                        "INVALID_CHARACTERISTIC_VALUE",
                        f"Value '{value}' is not allowed for characteristic '{characteristic['name']}'",
                    )
                )

    return reasons


def generate_query_product_configuration(payload: dict[str, Any]) -> dict[str, Any]:
    validation = validate_query_product_configuration(payload)
    request_items = payload.get("requestProductConfigurationItem") or []
    if not validation["valid"]:
        return {
            "validation": validation,
            "computedItems": [],
            "summary": {
                "requestedCount": len(request_items) if isinstance(request_items, list) else 0,
                "computedCount": 0,
                "approvedCount": 0,
                "rejectedCount": 0,
            },
        }

    computed_items: list[dict[str, Any]] = []
    approved_count = 0
    rejected_count = 0

    for index, item in enumerate(request_items, start=1):
        item_id = str(item.get("id") or index)
        requested_configuration = item.get("productConfiguration") or {}
        product_offering = requested_configuration.get("productOffering") or {}
        offering_id = product_offering.get("id")
        entry = STARTER_CATALOG_INDEX.get(str(offering_id))

        if not entry:
            rejected_count += 1
            computed_items.append(
                {
                    **_unknown_offering_item(str(index + 100), offering_id, "QueryProductConfiguration"),
                    "productConfigurationItemRelationship": [
                        {"@type": "ProductConfigurationItemRelationship", "id": item_id, "role": "requestItem"}
                    ],
                }
            )
            continue

        approved_count += 1
        computed_items.append(
            {
                "@type": "QueryProductConfigurationItem",
                "id": str(index + 100),
                "state": "approved",
                "productConfigurationItemRelationship": [
                    {"@type": "ProductConfigurationItemRelationship", "id": item_id, "role": "requestItem"}
                ],
                "productConfiguration": _normalize_product_configuration(
                    entry,
                    requested_configuration,
                    allow_defaults=True,
                ),
            }
        )

    return {
        "validation": validation,
        "computedItems": computed_items,
        "summary": {
            "requestedCount": len(request_items),
            "computedCount": len(computed_items),
            "approvedCount": approved_count,
            "rejectedCount": rejected_count,
        },
    }


def evaluate_check_product_configuration(payload: dict[str, Any]) -> dict[str, Any]:
    validation = validate_check_product_configuration(payload)
    check_items = payload.get("checkProductConfigurationItem") or []
    if not validation["valid"]:
        return {
            "validation": validation,
            "checkItems": [],
            "summary": {
                "checkedCount": 0,
                "acceptedCount": 0,
                "rejectedCount": 0,
            },
        }

    evaluated_items: list[dict[str, Any]] = []
    accepted_count = 0
    rejected_count = 0

    for index, item in enumerate(check_items, start=1):
        item_id = str(item.get("id") or index)
        requested_configuration = item.get("productConfiguration") or {}
        product_offering = requested_configuration.get("productOffering") or {}
        offering_id = product_offering.get("id")
        entry = STARTER_CATALOG_INDEX.get(str(offering_id))

        if not entry:
            rejected_count += 1
            evaluated_items.append(_unknown_offering_item(item_id, offering_id, "CheckProductConfiguration"))
            continue

        reasons = _validate_selected_configuration(entry, requested_configuration)
        item_document = {
            "@type": "CheckProductConfigurationItem",
            "id": item_id,
            "state": "accepted" if not reasons else "rejected",
            "productConfiguration": _normalize_product_configuration(
                entry,
                requested_configuration,
                allow_defaults=False,
            ),
        }
        if reasons:
            rejected_count += 1
            item_document["stateReason"] = reasons
            if payload.get("provideAlternatives"):
                item_document["alternateProductConfigurationProposal"] = [
                    _normalize_product_configuration(entry, None, allow_defaults=True)
                ]
        else:
            accepted_count += 1
        evaluated_items.append(item_document)

    return {
        "validation": validation,
        "checkItems": evaluated_items,
        "summary": {
            "checkedCount": len(evaluated_items),
            "acceptedCount": accepted_count,
            "rejectedCount": rejected_count,
        },
    }
