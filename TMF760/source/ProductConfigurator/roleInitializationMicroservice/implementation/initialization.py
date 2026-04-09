from __future__ import annotations

import os
import sys
import time

import httpx


def main() -> int:
    base_url = os.getenv("ROLE_API_BASE_URL", "http://localhost:8080/tmf-api/partyRoleManagement/v4").rstrip("/")
    canvas_system_role = os.getenv("CANVAS_SYSTEM_ROLE", "ProductConfiguratorAdmin")
    payload = {
        "name": canvas_system_role,
        "roleType": canvas_system_role,
        "state": "active",
        "description": "Bootstrap role for the TMFC027 Product Configurator component",
        "@type": "PartyRole",
    }

    with httpx.Client(timeout=5.0) as client:
        for attempt in range(1, 11):
            try:
                response = client.get(f"{base_url}/partyRole")
                response.raise_for_status()
                roles = response.json()
                if any(role.get("name") == canvas_system_role for role in roles):
                    print(f"Role '{canvas_system_role}' already exists")
                    return 0

                create_response = client.post(f"{base_url}/partyRole", json=payload)
                create_response.raise_for_status()
                print(f"Created bootstrap role '{canvas_system_role}'")
                return 0
            except Exception as exc:
                print(f"Role initialization attempt {attempt} failed: {exc}")
                time.sleep(3)

    print("Role initialization failed after retries", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
