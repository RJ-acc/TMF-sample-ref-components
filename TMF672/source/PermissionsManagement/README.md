# TMFC035 Permissions Management Source

This source tree follows the same reference-component layout used elsewhere in this repo, but implements a Python-based `TMFC035 Permissions Management` baseline for `TMF672 User Role Permission Management v4.0.0`.

Key folders:
- `permissionsManagementMicroservice/implementation`
  The core TMF672 API exposing list/create/get/patch for `permission` and `userRole`, plus `hub` and listener callbacks.
- `permissionsManagementEngineMicroservice/implementation`
  A lightweight validation and seed-data service used by the API as an optional helper.
- `common`
  Shared TMF672 resource metadata, seed documents, validation logic, storage helpers, and event utilities.
- `openMetricsMicroservice`
  Prometheus-text metrics listener for TMF672 permission-management events.
- `partyRoleMicroservice`
  Small TMF669 Party Role API used to bootstrap the component system role.
- `permissionsManagementInitializationMicroservice/implementation`
  Registers the metrics listener through the TMF672 `hub` endpoint.
- `MCPServerMicroservice`
  Optional MCP wrapper over the TMF672 API.

Local development:

```bash
pip install -r TMF672/source/PermissionsManagement/requirements.txt
```

Run the engine:

```bash
uvicorn permissionsManagementEngineMicroservice.implementation.app:app \
  --app-dir TMF672/source/PermissionsManagement \
  --port 8081 --reload
```

Run the API:

```bash
uvicorn permissionsManagementMicroservice.implementation.app:app \
  --app-dir TMF672/source/PermissionsManagement \
  --port 8080 --reload
```

Run the Party Role API:

```bash
uvicorn partyRoleMicroservice.implementation.app:app \
  --app-dir TMF672/source/PermissionsManagement \
  --port 8090 --reload
```

Run the metrics listener:

```bash
uvicorn openMetricsMicroservice.app:app \
  --app-dir TMF672/source/PermissionsManagement \
  --port 4000 --reload
```

Tests:

```bash
python3 -m unittest discover -s TMF672/source/PermissionsManagement/tests -v
```

This is a reference baseline, not a full TMF672 certification target. The implementation focuses on:
- the complete official TMF672 path surface
- spec-aligned behavior for `permission` and `userRole`
- listener registration and callback endpoints
- a simple deterministic data model that is easy to run locally and inside the chart
