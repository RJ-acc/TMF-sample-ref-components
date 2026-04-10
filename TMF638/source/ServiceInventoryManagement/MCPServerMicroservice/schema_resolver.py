from __future__ import annotations


def resolve_ref(ref: str, spec: dict) -> dict:
    if not ref.startswith("#/"):
        return {"description": f"External ref: {ref}"}

    current = spec
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict):
            return {}
        current = current.get(part, {})
    return current or {}


def resolve_schema(schema: dict, spec: dict, depth: int = 0, visited: set[str] | None = None) -> dict:
    if visited is None:
        visited = set()
    if not schema or not isinstance(schema, dict):
        return schema or {}
    if depth > 6:
        return {"type": "object", "description": "Schema depth limit reached"}

    if "$ref" in schema:
        ref = schema["$ref"]
        if ref in visited:
            return {"type": "object", "description": f"Circular ref: {ref}"}
        return resolve_schema(resolve_ref(ref, spec), spec, depth + 1, visited | {ref})

    result = {}
    for key, value in schema.items():
        if key == "properties" and isinstance(value, dict):
            result[key] = {
                property_name: resolve_schema(property_schema, spec, depth + 1, visited)
                for property_name, property_schema in value.items()
            }
        elif key == "items" and isinstance(value, dict):
            result[key] = resolve_schema(value, spec, depth + 1, visited)
        elif key == "allOf" and isinstance(value, list):
            merged_properties = {}
            merged_required = []
            for item in value:
                resolved = resolve_schema(item, spec, depth + 1, visited)
                merged_properties.update(resolved.get("properties", {}))
                merged_required.extend(resolved.get("required", []))
            result["type"] = "object"
            if merged_properties:
                result["properties"] = merged_properties
            if merged_required:
                result["required"] = sorted(set(merged_required))
        else:
            result[key] = value
    return result

