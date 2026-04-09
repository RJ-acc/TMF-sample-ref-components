from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException

from common.access import ensure_seed_data, resource_collection, resource_names
from common.store import get_store
from common.validation import validate_create_payload, validate_patch_payload

app = FastAPI(title="TMFC035 Permissions Management Engine Service")
store = get_store()


def _seed() -> None:
    ensure_seed_data(store)


@app.get("/health")
async def health() -> dict[str, Any]:
    _seed()
    return {"status": "ok", "backend": store.backend}


@app.get("/{resource_name}")
async def list_seeded_resource(resource_name: str) -> dict[str, Any]:
    _seed()
    if resource_name not in resource_names():
        raise HTTPException(status_code=404, detail=f"Resource '{resource_name}' is not supported")
    items = store.list_documents(resource_collection(resource_name))
    return {"resource": resource_name, "count": len(items), "items": items}


@app.post("/validate/{resource_name}")
async def validate_create(resource_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    return validate_create_payload(resource_name, payload)


@app.post("/validate/{resource_name}/patch")
async def validate_patch(resource_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    return validate_patch_payload(resource_name, payload)
