from __future__ import annotations

from typing import Any


def build_api_directory(
    *,
    base_path: str,
    title: str,
    version: str,
    description: str,
    operations: list[dict[str, str]],
) -> dict[str, Any]:
    normalized_base = "/" + base_path.strip("/")
    links: dict[str, Any] = {
        "self": {
            "href": f"{normalized_base}/",
            "description": description,
            "title": title,
            "version": version,
        }
    }

    for operation in operations:
        href = operation["href"]
        if not href.startswith("/"):
            href = f"/{href}"
        links[operation["name"]] = {
            "href": f"{normalized_base}{href}",
            "method": operation["method"],
            "description": operation["description"],
        }

    return {"_links": links}
