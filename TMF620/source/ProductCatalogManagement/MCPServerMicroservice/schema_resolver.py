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


def _merge_schema(target: dict, source: dict) -> dict:
    for key, value in source.items():
        if key == "required" and isinstance(value, list):
            target[key] = sorted(set(target.get(key, [])) | set(value))
        elif key == "properties" and isinstance(value, dict) and isinstance(target.get(key), dict):
            target[key].update(value)
        elif key not in target:
            target[key] = value
    return target


def resolve_schema(schema: dict, spec: dict, visited: set[str] | None = None) -> dict:
    if visited is None:
        visited = set()
    if not schema or not isinstance(schema, dict):
        return schema or {}

    if "$ref" in schema:
        ref = schema["$ref"]
        if ref in visited:
            return {"type": "object", "description": f"Circular ref: {ref}"}
        resolved = resolve_schema(resolve_ref(ref, spec), spec, visited | {ref})
        siblings = {key: value for key, value in schema.items() if key != "$ref"}
        if not siblings:
            return resolved
        return _merge_schema(dict(resolved), resolve_schema(siblings, spec, visited))

    result = {}
    for key, value in schema.items():
        if key == "properties" and isinstance(value, dict):
            result[key] = {
                property_name: resolve_schema(property_schema, spec, visited)
                for property_name, property_schema in value.items()
            }
        elif key == "items" and isinstance(value, dict):
            result[key] = resolve_schema(value, spec, visited)
        elif key == "allOf" and isinstance(value, list):
            merged = {}
            for item in value:
                _merge_schema(merged, resolve_schema(item, spec, visited))
            _merge_schema(result, merged)
        elif key in {"oneOf", "anyOf"} and isinstance(value, list):
            result[key] = [resolve_schema(item, spec, visited) for item in value]
        elif key == "discriminator" and isinstance(value, dict):
            discriminator = {name: item for name, item in value.items() if name != "mapping"}
            if discriminator:
                result[key] = discriminator
        elif key in {"not", "additionalProperties", "propertyNames", "contains"} and isinstance(value, dict):
            result[key] = resolve_schema(value, spec, visited)
        else:
            result[key] = value
    return result
