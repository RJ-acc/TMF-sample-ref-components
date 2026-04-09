from __future__ import annotations

import re

import mcp.types as types

from schema_resolver import resolve_ref, resolve_schema

RESOURCE_HINTS = {
    "billformat": "Bill Format defines how a bill is rendered or encoded for delivery.",
    "billpresentationmedia": "Bill Presentation Media captures the preferred delivery medium for bills.",
    "billingaccount": "Billing Account manages the commercial account used for invoicing and balance tracking.",
    "billingcyclespecification": "Billing Cycle Specification describes the cadence used to issue bills.",
    "financialaccount": "Financial Account represents the ledger-style account used for receivables or accounting.",
    "partyaccount": "Party Account links account records to a party or customer context.",
    "settlementaccount": "Settlement Account captures the account used for settlement and payout flows.",
    "hub": "The Hub resource manages event subscriptions for TMF666 notifications.",
}


def _to_snake_case(name: str) -> str:
    first_pass = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", first_pass).lower()


def _infer_resource_hint(path: str) -> str:
    segments = [segment for segment in path.strip("/").split("/") if not segment.startswith("{")]
    resource = segments[-1].lower() if segments else ""
    return RESOURCE_HINTS.get(resource, "")


def _build_input_schema(operation: dict, spec: dict, method: str) -> dict:
    properties = {}
    required = []

    for raw_param in operation.get("parameters", []):
        parameter = resolve_ref(raw_param["$ref"], spec) if "$ref" in raw_param else raw_param
        name = parameter.get("name")
        if not name:
            continue

        location = parameter.get("in", "query")
        is_required = parameter.get("required", False) or location == "path"
        description = parameter.get("description", "")
        parameter_schema = parameter.get("schema") or {
            key: value
            for key, value in parameter.items()
            if key in {"type", "format", "enum", "default", "minimum", "maximum", "pattern"}
        }
        resolved = resolve_schema(parameter_schema, spec) if parameter_schema else {"type": "string"}
        if description:
            resolved["description"] = description
        resolved["x-param-location"] = location
        properties[name] = resolved
        if is_required:
            required.append(name)

    if method in {"post", "patch", "put"}:
        body_schema = {}
        if operation.get("requestBody"):
            request_body = operation["requestBody"]
            if "$ref" in request_body:
                request_body = resolve_ref(request_body["$ref"], spec)
            content = request_body.get("content", {})
            for media_type in ("application/json", "application/merge-patch+json", "application/json-patch+json"):
                media = content.get(media_type)
                if media and media.get("schema"):
                    body_schema = media["schema"]
                    break

        if body_schema:
            resolved_body = resolve_schema(body_schema, spec)
            for name, body_property in resolved_body.get("properties", {}).items():
                properties[name] = {**body_property, "x-param-location": "body"}
            required.extend(resolved_body.get("required", []))

    schema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = sorted(set(required))
    return schema


def generate_tools(spec: dict) -> dict[str, dict]:
    registry = {}
    for path, path_item in spec.get("paths", {}).items():
        if path.startswith("/listener/"):
            continue
        if not isinstance(path_item, dict):
            continue

        for method, operation in path_item.items():
            if method not in {"get", "post", "patch", "delete", "put"} or not isinstance(operation, dict):
                continue

            operation_id = operation.get("operationId")
            if not operation_id:
                continue

            tool_name = _to_snake_case(operation_id)
            description_parts = []
            if operation.get("summary"):
                description_parts.append(operation["summary"].strip())
            if operation.get("description") and operation["description"].strip() != operation.get("summary", "").strip():
                description_parts.append(operation["description"].strip())
            resource_hint = _infer_resource_hint(path)
            if resource_hint:
                description_parts.append(f"About this resource: {resource_hint}")
            description_parts.append(f"TMF666 operation: {method.upper()} {path}")

            registry[tool_name] = {
                "operation_id": operation_id,
                "path": path,
                "method": method,
                "parameters": operation.get("parameters", []),
                "tool": types.Tool(
                    name=tool_name,
                    description="\n\n".join(description_parts),
                    inputSchema=_build_input_schema(operation, spec, method),
                ),
            }

    return registry
