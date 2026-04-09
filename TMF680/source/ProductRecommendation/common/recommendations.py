from __future__ import annotations

from typing import Any

from common.validation import validate_query_product_recommendation

STARTER_CATALOG = [
    {
        "id": "offer-5g-premium",
        "name": "5G Premium Unlimited",
        "category": "mobile",
        "channels": {"web", "mobile-app", "retail"},
        "types": {"upsell", "retention"},
        "score": 95,
    },
    {
        "id": "offer-family-share",
        "name": "Family Share Add-on",
        "category": "bundles",
        "channels": {"web", "retail", "call-center"},
        "types": {"cross-sell", "upsell"},
        "score": 90,
    },
    {
        "id": "offer-device-protect",
        "name": "Device Protection Plus",
        "category": "insurance",
        "channels": {"web", "mobile-app", "retail"},
        "types": {"cross-sell", "retention"},
        "score": 88,
    },
    {
        "id": "offer-streaming-bundle",
        "name": "Streaming Bundle",
        "category": "entertainment",
        "channels": {"web", "mobile-app"},
        "types": {"cross-sell", "next-best-action"},
        "score": 86,
    },
    {
        "id": "offer-fiber-upgrade",
        "name": "Fiber 1 Gbps Upgrade",
        "category": "broadband",
        "channels": {"web", "call-center", "partner"},
        "types": {"upsell", "replacement"},
        "score": 92,
    },
    {
        "id": "offer-loyalty-discount",
        "name": "Loyalty Discount Refresh",
        "category": "loyalty",
        "channels": {"call-center", "retail"},
        "types": {"retention", "next-best-action"},
        "score": 84,
    },
]

TYPE_CATEGORY_HINTS = {
    "upsell": {"mobile", "broadband", "bundles"},
    "cross-sell": {"insurance", "entertainment", "bundles"},
    "retention": {"loyalty", "mobile", "insurance"},
    "replacement": {"broadband", "mobile"},
    "next-best-action": {"entertainment", "loyalty", "bundles"},
}


def _normalize_token(value: Any) -> str:
    return str(value or "").strip().lower()


def _category_tokens(payload: dict[str, Any]) -> set[str]:
    categories = set()
    for category in payload.get("category") or []:
        if not isinstance(category, dict):
            continue
        for key in ("id", "name", "@referredType"):
            token = _normalize_token(category.get(key))
            if token:
                categories.add(token)
    recommendation_type = _normalize_token(payload.get("recommendationType"))
    categories.update(TYPE_CATEGORY_HINTS.get(recommendation_type, set()))
    return categories


def _channel_tokens(payload: dict[str, Any]) -> set[str]:
    channels = set()
    for channel in payload.get("channel") or []:
        if not isinstance(channel, dict):
            continue
        for key in ("id", "name", "role"):
            token = _normalize_token(channel.get(key))
            if token:
                channels.add(token)
    return channels


def _cart_tokens(payload: dict[str, Any]) -> set[str]:
    tokens = set()
    for cart in payload.get("shoppingCart") or []:
        if isinstance(cart, dict):
            tokens.update({_normalize_token(cart.get("id")), _normalize_token(cart.get("name"))})
    for item in payload.get("shoppingCartItem") or []:
        if isinstance(item, dict):
            tokens.update({_normalize_token(item.get("id")), _normalize_token(item.get("name"))})
    return {token for token in tokens if token}


def _score_catalog_item(
    item: dict[str, Any],
    category_tokens: set[str],
    channel_tokens: set[str],
    cart_tokens: set[str],
) -> int:
    score = item["score"]
    if category_tokens and item["category"] in category_tokens:
        score += 25
    if channel_tokens and item["channels"].intersection(channel_tokens):
        score += 15
    if channel_tokens and not item["channels"].intersection(channel_tokens):
        score -= 5
    if cart_tokens and any(token in item["name"].lower() for token in cart_tokens):
        score -= 10
    return score


def _build_recommendation_item(item: dict[str, Any], priority: int) -> dict[str, Any]:
    return {
        "id": item["id"],
        "priority": priority,
        "product": {
            "id": f"product-{item['id']}",
            "name": item["name"],
            "@type": "ProductRefOrValue",
        },
        "productOffering": {
            "id": item["id"],
            "name": item["name"],
            "@referredType": "ProductOffering",
        },
        "@type": "RecommendationItem",
    }


def generate_recommendations(payload: dict[str, Any], *, limit: int = 3) -> dict[str, Any]:
    validation = validate_query_product_recommendation(payload)
    category_tokens = _category_tokens(payload)
    channel_tokens = _channel_tokens(payload)
    cart_tokens = _cart_tokens(payload)

    ranked = sorted(
        STARTER_CATALOG,
        key=lambda item: (
            _score_catalog_item(item, category_tokens, channel_tokens, cart_tokens),
            item["score"],
            item["name"],
        ),
        reverse=True,
    )
    selected = ranked[: max(limit, 1)]

    return {
        "validation": validation,
        "recommendationItems": [
            _build_recommendation_item(item, priority=index)
            for index, item in enumerate(selected, start=1)
        ],
        "summary": {
            "catalogSize": len(STARTER_CATALOG),
            "matchedCategories": sorted(category_tokens),
            "matchedChannels": sorted(channel_tokens),
            "shoppingContextTokens": sorted(cart_tokens),
        },
    }
