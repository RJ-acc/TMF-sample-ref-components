from __future__ import annotations

from typing import Any

import httpx

from config import config


def _split_arguments(path: str, parameters: list[dict], arguments: dict[str, Any]) -> tuple[dict, dict, dict]:
    path_params = {}
    query_params = {}
    body = {}

    locations = {}
    body_parameter_names = set()
    for parameter in parameters:
        if isinstance(parameter, dict) and "$ref" not in parameter and parameter.get("name"):
            locations[parameter["name"]] = parameter.get("in", "query")
            if parameter.get("in") == "body":
                body_parameter_names.add(parameter["name"])

    for key, value in arguments.items():
        location = locations.get(key)
        if location == "path" or (location is None and f"{{{key}}}" in path):
            path_params[key] = value
        elif location == "query":
            query_params[key] = value
        else:
            body[key] = value

    if len(body) == 1:
        body_key, body_value = next(iter(body.items()))
        if body_key in body_parameter_names and isinstance(body_value, dict):
            body = body_value

    return path_params, query_params, body


async def execute_tool(path: str, method: str, parameters: list[dict], arguments: dict[str, Any]) -> dict:
    path_params, query_params, body = _split_arguments(path, parameters, arguments)

    filled_path = path
    for key, value in path_params.items():
        filled_path = filled_path.replace(f"{{{key}}}", str(value))

    url = f"{config.BASE_URL.rstrip('/')}{config.api_base_path}{filled_path}"
    headers = {
        "Accept": "application/json;charset=utf-8",
        "Content-Type": "application/json",
    }
    if config.API_TOKEN:
        headers["Authorization"] = f"Bearer {config.API_TOKEN}"

    try:
        async with httpx.AsyncClient(timeout=config.TIMEOUT_SECONDS, verify=config.VERIFY_SSL) as client:
            response = await client.request(
                method.upper(),
                url,
                params=query_params or None,
                json=body if body and method in {"post", "patch", "put"} else None,
                headers=headers,
            )

        try:
            payload = response.json()
        except Exception:
            payload = {"raw_text": response.text}

        if response.is_success:
            return {"success": True, "http_status": response.status_code, "data": payload}
        return {"success": False, "http_status": response.status_code, "error": payload}
    except Exception as exc:
        return {
            "success": False,
            "http_status": 500,
            "error": {"code": "EXECUTION_FAILED", "message": str(exc)},
        }
