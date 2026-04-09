from __future__ import annotations

from typing import Any
from uuid import uuid4

from common.events import utc_now

DEFAULT_API_BASE_PATH = "/tmf-api/productCatalogManagement/v5"
DEFAULT_SEED_TIMESTAMP = "2026-04-09T00:00:00Z"
CATALOG_STATES = {
    "active",
    "inactive",
    "launched",
    "obsolete",
    "draft",
    "designed",
    "inProgress",
    "completed",
    "failed",
}

RESOURCE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "productCatalog": {
        "collection": "product_catalogs",
        "type": "ProductCatalog",
        "id_prefix": "product-catalog",
        "default_state": "active",
        "patchable": True,
        "listener_suffixes": (
            "AttributeValueChangeEvent",
            "CreateEvent",
            "DeleteEvent",
            "StateChangeEvent",
        ),
        "defaults": {
            "lifecycleStatus": "Launched",
            "version": "1.0",
        },
    },
    "category": {
        "collection": "categories",
        "type": "Category",
        "id_prefix": "category",
        "default_state": "active",
        "patchable": True,
        "listener_suffixes": (
            "AttributeValueChangeEvent",
            "CreateEvent",
            "DeleteEvent",
            "StateChangeEvent",
        ),
        "defaults": {
            "isRoot": False,
            "version": "1.0",
        },
    },
    "productOffering": {
        "collection": "product_offerings",
        "type": "ProductOffering",
        "id_prefix": "product-offering",
        "default_state": "active",
        "patchable": True,
        "listener_suffixes": (
            "AttributeValueChangeEvent",
            "CreateEvent",
            "DeleteEvent",
            "StateChangeEvent",
        ),
        "defaults": {
            "isBundle": False,
            "lifecycleStatus": "Launched",
            "version": "1.0",
        },
    },
    "productOfferingPrice": {
        "collection": "product_offering_prices",
        "type": "ProductOfferingPrice",
        "id_prefix": "product-offering-price",
        "default_state": "active",
        "patchable": True,
        "listener_suffixes": (
            "AttributeValueChangeEvent",
            "CreateEvent",
            "DeleteEvent",
            "StateChangeEvent",
        ),
        "defaults": {
            "priceType": "recurring",
            "recurringChargePeriod": "month",
        },
    },
    "productSpecification": {
        "collection": "product_specifications",
        "type": "ProductSpecification",
        "id_prefix": "product-specification",
        "default_state": "active",
        "patchable": True,
        "listener_suffixes": (
            "AttributeValueChangeEvent",
            "CreateEvent",
            "DeleteEvent",
            "StateChangeEvent",
        ),
        "defaults": {
            "isBundle": False,
            "lifecycleStatus": "Launched",
            "version": "1.0",
        },
    },
    "importJob": {
        "collection": "import_jobs",
        "type": "ImportJob",
        "id_prefix": "import-job",
        "default_state": "completed",
        "patchable": False,
        "listener_suffixes": (
            "CreateEvent",
            "StateChangeEvent",
        ),
        "defaults": {
            "status": "completed",
            "contentType": "application/json",
        },
    },
    "exportJob": {
        "collection": "export_jobs",
        "type": "ExportJob",
        "id_prefix": "export-job",
        "default_state": "completed",
        "patchable": False,
        "listener_suffixes": (
            "CreateEvent",
            "StateChangeEvent",
        ),
        "defaults": {
            "status": "completed",
            "contentType": "application/json",
        },
    },
}

CRUD_RESOURCE_ORDER = (
    "productCatalog",
    "category",
    "productOffering",
    "productOfferingPrice",
    "productSpecification",
)
TASK_RESOURCE_ORDER = ("importJob", "exportJob")
RESOURCE_ORDER = CRUD_RESOURCE_ORDER + TASK_RESOURCE_ORDER


def resource_names() -> tuple[str, ...]:
    return RESOURCE_ORDER


def crud_resource_names() -> tuple[str, ...]:
    return CRUD_RESOURCE_ORDER


def task_resource_names() -> tuple[str, ...]:
    return TASK_RESOURCE_ORDER


def get_resource_definition(resource_name: str) -> dict[str, Any]:
    try:
        return RESOURCE_DEFINITIONS[resource_name]
    except KeyError as exc:
        raise KeyError(f"Unknown TMF620 resource '{resource_name}'") from exc


def resource_type(resource_name: str) -> str:
    return get_resource_definition(resource_name)["type"]


def resource_collection(resource_name: str) -> str:
    return get_resource_definition(resource_name)["collection"]


def resource_href(resource_name: str, entity_id: str, base_path: str = DEFAULT_API_BASE_PATH) -> str:
    return f"{base_path.rstrip('/')}/{resource_name}/{entity_id}"


def supports_patch(resource_name: str) -> bool:
    return bool(get_resource_definition(resource_name)["patchable"])


def listener_suffixes(resource_name: str) -> tuple[str, ...]:
    return tuple(get_resource_definition(resource_name)["listener_suffixes"])


def listener_event_types() -> list[str]:
    return [
        f"{resource_type(resource_name)}{suffix}"
        for resource_name in RESOURCE_ORDER
        for suffix in listener_suffixes(resource_name)
    ]


def supports_event(resource_name: str, suffix: str) -> bool:
    return suffix in listener_suffixes(resource_name)


def _ensure_ref(
    target_resource: str,
    reference: dict[str, Any],
    base_path: str,
    *,
    referred_type: str | None = None,
) -> None:
    if not isinstance(reference, dict) or not reference.get("id"):
        return
    reference.setdefault("href", resource_href(target_resource, reference["id"], base_path))
    reference.setdefault("@referredType", referred_type or resource_type(target_resource))


def _normalize_references(resource_name: str, document: dict[str, Any], base_path: str) -> None:
    if resource_name == "category":
        _ensure_ref("productCatalog", document.get("productCatalog"), base_path, referred_type="ProductCatalog")
        return

    if resource_name == "productOffering":
        _ensure_ref("productCatalog", document.get("productCatalog"), base_path, referred_type="ProductCatalog")
        _ensure_ref("productSpecification", document.get("productSpecification"), base_path, referred_type="ProductSpecification")
        categories = document.get("category")
        if isinstance(categories, list):
            for category in categories:
                _ensure_ref("category", category, base_path, referred_type="Category")
        prices = document.get("productOfferingPrice")
        if isinstance(prices, list):
            for price in prices:
                _ensure_ref("productOfferingPrice", price, base_path, referred_type="ProductOfferingPrice")
        return

    if resource_name == "productOfferingPrice":
        _ensure_ref("productOffering", document.get("productOffering"), base_path, referred_type="ProductOffering")
        return

    if resource_name == "productSpecification":
        catalogs = document.get("productCatalog")
        if isinstance(catalogs, list):
            for catalog in catalogs:
                _ensure_ref("productCatalog", catalog, base_path, referred_type="ProductCatalog")


def _base_entity(
    resource_name: str,
    entity_id: str,
    name: str,
    base_path: str,
    **fields: Any,
) -> dict[str, Any]:
    metadata = get_resource_definition(resource_name)
    state = fields.pop("state", metadata["default_state"])
    status = fields.pop("status", state)
    document = {
        **metadata["defaults"],
        **fields,
        "id": entity_id,
        "href": resource_href(resource_name, entity_id, base_path),
        "name": name,
        "state": state,
        "status": status,
        "lastUpdate": fields.pop("lastUpdate", DEFAULT_SEED_TIMESTAMP),
        "@type": metadata["type"],
    }
    _normalize_references(resource_name, document, base_path)
    return document


def _seed_documents(base_path: str) -> dict[str, list[dict[str, Any]]]:
    return {
        "product_catalogs": [
            _base_entity(
                "productCatalog",
                "product-catalog-retail",
                "Retail Broadband Catalog",
                base_path,
                description="Retail catalog for broadband and managed Wi-Fi offers.",
            ),
            _base_entity(
                "productCatalog",
                "product-catalog-business",
                "Business Connectivity Catalog",
                base_path,
                description="Business catalog for secure access and managed connectivity.",
            ),
        ],
        "categories": [
            _base_entity(
                "category",
                "category-broadband",
                "Broadband",
                base_path,
                description="Broadband access offers for residential customers.",
                isRoot=True,
                productCatalog={"id": "product-catalog-retail"},
            ),
            _base_entity(
                "category",
                "category-managed-wifi",
                "Managed Wi-Fi",
                base_path,
                description="Managed Wi-Fi extensions and add-ons.",
                productCatalog={"id": "product-catalog-retail"},
            ),
        ],
        "product_specifications": [
            _base_entity(
                "productSpecification",
                "product-specification-fiber-100",
                "Fiber 100",
                base_path,
                description="Fiber broadband product specification with 100 Mbps service profile.",
                brand="Contoso Fiber",
                lifecycleStatus="Launched",
                productNumber="FIBER-100",
                productCatalog=[{"id": "product-catalog-retail"}],
            ),
            _base_entity(
                "productSpecification",
                "product-specification-managed-wifi",
                "Managed Wi-Fi Plus",
                base_path,
                description="Managed Wi-Fi add-on with advanced diagnostics and mesh support.",
                brand="Contoso Fiber",
                lifecycleStatus="Launched",
                productNumber="WIFI-PLUS",
                productCatalog=[{"id": "product-catalog-retail"}],
            ),
        ],
        "product_offerings": [
            _base_entity(
                "productOffering",
                "product-offering-fiber-100",
                "Fiber 100 Monthly",
                base_path,
                description="Retail monthly offer for the Fiber 100 specification.",
                isSellable=True,
                productCatalog={"id": "product-catalog-retail"},
                category=[{"id": "category-broadband"}],
                productSpecification={"id": "product-specification-fiber-100"},
                productOfferingPrice=[{"id": "product-offering-price-fiber-100-monthly"}],
            ),
            _base_entity(
                "productOffering",
                "product-offering-managed-wifi",
                "Managed Wi-Fi Plus Add-on",
                base_path,
                description="Add-on offer for extended managed Wi-Fi capability.",
                isSellable=True,
                productCatalog={"id": "product-catalog-retail"},
                category=[{"id": "category-managed-wifi"}],
                productSpecification={"id": "product-specification-managed-wifi"},
                productOfferingPrice=[{"id": "product-offering-price-managed-wifi-monthly"}],
            ),
        ],
        "product_offering_prices": [
            _base_entity(
                "productOfferingPrice",
                "product-offering-price-fiber-100-monthly",
                "Fiber 100 Monthly Price",
                base_path,
                description="Monthly recurring charge for Fiber 100.",
                price={"taxIncludedAmount": {"unit": "USD", "value": 59.99}},
                priceType="recurring",
                recurringChargePeriod="month",
                productOffering={"id": "product-offering-fiber-100"},
            ),
            _base_entity(
                "productOfferingPrice",
                "product-offering-price-managed-wifi-monthly",
                "Managed Wi-Fi Monthly Price",
                base_path,
                description="Monthly recurring charge for Managed Wi-Fi Plus.",
                price={"taxIncludedAmount": {"unit": "USD", "value": 12.5}},
                priceType="recurring",
                recurringChargePeriod="month",
                productOffering={"id": "product-offering-managed-wifi"},
            ),
        ],
        "import_jobs": [
            _base_entity(
                "importJob",
                "import-job-retail-001",
                "Retail Catalog Import",
                base_path,
                description="Seed import job for retail catalog content.",
                status="completed",
                state="completed",
                contentType="application/json",
                url="https://catalog.example.com/imports/retail-001.json",
            ),
            _base_entity(
                "importJob",
                "import-job-business-001",
                "Business Catalog Import",
                base_path,
                description="Seed import job for business catalog content.",
                status="completed",
                state="completed",
                contentType="application/json",
                url="https://catalog.example.com/imports/business-001.json",
            ),
        ],
        "export_jobs": [
            _base_entity(
                "exportJob",
                "export-job-retail-001",
                "Retail Catalog Export",
                base_path,
                description="Seed export job for retail catalog distribution.",
                status="completed",
                state="completed",
                contentType="application/json",
                url="https://catalog.example.com/exports/retail-001.json",
            ),
            _base_entity(
                "exportJob",
                "export-job-business-001",
                "Business Catalog Export",
                base_path,
                description="Seed export job for business catalog distribution.",
                status="completed",
                state="completed",
                contentType="application/json",
                url="https://catalog.example.com/exports/business-001.json",
            ),
        ],
    }


def ensure_seed_data(store: Any, base_path: str = DEFAULT_API_BASE_PATH) -> None:
    if store.list_documents(resource_collection("productCatalog"), limit=1):
        return

    seed_documents = _seed_documents(base_path)
    for metadata in RESOURCE_DEFINITIONS.values():
        collection = metadata["collection"]
        for document in seed_documents[collection]:
            try:
                store.create_document(collection, document)
            except ValueError:
                continue


def build_entity(resource_name: str, payload: dict[str, Any], base_path: str = DEFAULT_API_BASE_PATH) -> dict[str, Any]:
    metadata = get_resource_definition(resource_name)
    entity_id = payload.get("id") or f"{metadata['id_prefix']}-{uuid4().hex[:8]}"
    state = payload.get("state", metadata["default_state"])
    entity = {
        **metadata["defaults"],
        **payload,
        "id": entity_id,
        "href": resource_href(resource_name, entity_id, base_path),
        "name": payload.get("name") or f"{metadata['type']} {entity_id}",
        "state": state,
        "status": payload.get("status", state),
        "lastUpdate": utc_now(),
        "@type": payload.get("@type", metadata["type"]),
    }
    _normalize_references(resource_name, entity, base_path)
    return entity


def apply_patch(
    resource_name: str,
    existing: dict[str, Any],
    patch: dict[str, Any],
    base_path: str = DEFAULT_API_BASE_PATH,
) -> dict[str, Any]:
    metadata = get_resource_definition(resource_name)
    state = patch.get("state", existing.get("state", metadata["default_state"]))
    updated = {
        **existing,
        **patch,
        "id": existing["id"],
        "href": resource_href(resource_name, existing["id"], base_path),
        "state": state,
        "status": patch.get("status", patch.get("state", existing.get("status", state))),
        "lastUpdate": utc_now(),
        "@type": existing.get("@type", metadata["type"]),
    }
    _normalize_references(resource_name, updated, base_path)
    return updated
