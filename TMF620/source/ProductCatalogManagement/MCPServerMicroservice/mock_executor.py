from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id() -> str:
    return str(uuid4())[:8]


RESOURCE_DEFAULTS = {
    "productcatalog": {"@type": "ProductCatalog", "name": "Mock product catalog", "state": "active"},
    "category": {"@type": "Category", "name": "Mock category", "state": "active"},
    "productoffering": {"@type": "ProductOffering", "name": "Mock product offering", "state": "active"},
    "productofferingprice": {"@type": "ProductOfferingPrice", "name": "Mock product offering price", "state": "active"},
    "productspecification": {"@type": "ProductSpecification", "name": "Mock product specification", "state": "active"},
    "importjob": {"@type": "ImportJob", "name": "Mock import job", "state": "completed"},
    "exportjob": {"@type": "ExportJob", "name": "Mock export job", "state": "completed"},
    "hub": {"@type": "EventSubscription"},
}


def _infer_resource(path: str) -> str:
    segments = [segment for segment in path.strip("/").split("/") if not segment.startswith("{")]
    return segments[-1].lower() if segments else "unknown"


def _is_collection_path(path: str) -> bool:
    return "{" not in path


def _build_mock_item(resource: str, resource_id: str, arguments: dict[str, object], path: str) -> dict[str, object]:
    collection_path = path.split("{")[0].rstrip("/")
    item = {
        "id": resource_id,
        "href": f"/tmf-api/productCatalogManagement/v5{collection_path}/{resource_id}",
        "lastUpdate": _now(),
        **RESOURCE_DEFAULTS.get(resource, {"@type": resource}),
    }
    for key, value in arguments.items():
        if key not in {"id", "fields", "offset", "limit"}:
            item[key] = value
    return item


def mock_execute(path: str, method: str, arguments: dict[str, object]) -> dict:
    resource = _infer_resource(path)
    is_collection = _is_collection_path(path)
    resource_id = arguments.get("id", _new_id())
    note = "MOCK MODE - responses are synthetic. Set TMF620_MODE=live for real API calls."

    if method == "get":
        if is_collection:
            return {
                "success": True,
                "http_status": 200,
                "data": [_build_mock_item(resource, _new_id(), arguments, path)],
                "total_count": 1,
                "note": note,
            }
        return {
            "success": True,
            "http_status": 200,
            "data": _build_mock_item(resource, str(resource_id), arguments, path),
            "note": note,
        }

    if method in {"post", "patch"}:
        return {
            "success": True,
            "http_status": 200 if method == "patch" else 201,
            "data": _build_mock_item(resource, _new_id(), arguments, path),
            "note": note,
        }

    if method == "delete":
        return {
            "success": True,
            "http_status": 204,
            "data": None,
            "note": note,
        }

    return {
        "success": False,
        "http_status": 405,
        "error": {"message": f"HTTP method '{method}' is not supported"},
    }
