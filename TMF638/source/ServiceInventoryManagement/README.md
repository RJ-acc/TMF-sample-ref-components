# TMFC008 Service Inventory Management Source

This source tree follows the same reference-component layout used elsewhere in this repo, but implements a Python-based `TMFC008 Service Inventory Management` baseline for `TMF638 Service Inventory v5.0.0`.

Key folders:
- `serviceInventoryManagementMicroservice/implementation`
  The core TMF638 API exposing CRUD for `service`, plus `hub` and listener callbacks.
- `serviceInventoryManagementEngineMicroservice/implementation`
  A lightweight validation and seed-data service used by the API as an optional helper.
- `common`
  Shared TMF638 resource metadata, seed documents, validation logic, storage helpers, and event utilities.
- `openMetricsMicroservice`
  Prometheus-text metrics listener for TMF638 service-inventory events.
- `partyRoleMicroservice`
  Small TMF669 Party Role API used to bootstrap the component system role.
- `serviceInventoryManagementInitializationMicroservice/implementation`
  Registers the metrics listener through the TMF638 `hub` endpoint.
- `MCPServerMicroservice`
  Optional MCP wrapper over the TMF638 API.

Local development:

```bash
pip install -r TMF638/source/ServiceInventoryManagement/requirements.txt
```

Run the engine:

```bash
uvicorn serviceInventoryManagementEngineMicroservice.implementation.app:app \
  --app-dir TMF638/source/ServiceInventoryManagement \
  --port 8081 --reload
```

Run the API:

```bash
uvicorn serviceInventoryManagementMicroservice.implementation.app:app \
  --app-dir TMF638/source/ServiceInventoryManagement \
  --port 8080 --reload
```

Run the Party Role API:

```bash
uvicorn partyRoleMicroservice.implementation.app:app \
  --app-dir TMF638/source/ServiceInventoryManagement \
  --port 8090 --reload
```

Run the metrics listener:

```bash
uvicorn openMetricsMicroservice.app:app \
  --app-dir TMF638/source/ServiceInventoryManagement \
  --port 4000 --reload
```

Tests:

```bash
python3 -m unittest discover -s TMF638/source/ServiceInventoryManagement/tests -v
```

This is a reference baseline, not a full TMF638 certification target. The implementation focuses on:
- the complete official TMF638 path surface
- spec-aligned CRUD behavior for `service`
- listener registration and callback endpoints
- a simple deterministic data model that is easy to run locally and inside the chart
