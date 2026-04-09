from __future__ import annotations

import json
from pathlib import Path

import httpx
import yaml

from config import config

_spec_cache: dict | None = None


async def load_spec() -> dict:
    global _spec_cache

    if _spec_cache is not None:
        return _spec_cache

    cache_path = Path(config.SPEC_CACHE)
    if cache_path.exists():
        with cache_path.open(encoding="utf-8") as handle:
            if cache_path.suffix.lower() in {".yaml", ".yml"}:
                _spec_cache = yaml.safe_load(handle)
            else:
                _spec_cache = json.load(handle)
        return _spec_cache

    async with httpx.AsyncClient(timeout=60, verify=config.VERIFY_SSL) as client:
        response = await client.get(config.SPEC_URL)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "json" in content_type or config.SPEC_URL.endswith(".json"):
            _spec_cache = response.json()
        else:
            _spec_cache = yaml.safe_load(response.text)

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("w", encoding="utf-8") as handle:
        json.dump(_spec_cache, handle, indent=2)
    return _spec_cache
