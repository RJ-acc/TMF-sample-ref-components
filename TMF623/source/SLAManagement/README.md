# TMF623 SLA Management Source

This source tree follows the same reference-component layout used elsewhere in this repo, but implements a Python-based `TMF623 SLA Management` baseline for the classic `TMF623 SLA Management v2.0` resource surface.

Key folders:
- `slaManagementMicroservice/implementation`
  The core TMF623 API exposing list/create/get/delete/put/patch for `sla` and `slaViolation`, plus `hub` and listener callbacks.
- `slaManagementEngineMicroservice/implementation`
  A lightweight validation and seed-data service used by the API as an optional helper.
- `common`
  Shared TMF623 resource metadata, seed documents, validation logic, storage helpers, and event utilities.
- `openMetricsMicroservice`
  Prometheus-text metrics listener for TMF623 SLA-management events.
- `partyRoleMicroservice`
  Small TMF669 Party Role API used to bootstrap the component system role.
- `slaManagementInitializationMicroservice/implementation`
  Registers the metrics listener through the TMF623 `hub` endpoint.
- `MCPServerMicroservice`
  Optional MCP wrapper over the TMF623 API. A local spec cache is bundled so the server can start without fetching the swagger first.

Local development:

```bash
pip install -r TMF623/source/SLAManagement/requirements.txt
```

Run the engine:

```bash
uvicorn slaManagementEngineMicroservice.implementation.app:app \
  --app-dir TMF623/source/SLAManagement \
  --port 8081 --reload
```

Run the API:

```bash
uvicorn slaManagementMicroservice.implementation.app:app \
  --app-dir TMF623/source/SLAManagement \
  --port 8080 --reload
```

Run the Party Role API:

```bash
uvicorn partyRoleMicroservice.implementation.app:app \
  --app-dir TMF623/source/SLAManagement \
  --port 8090 --reload
```

Run the metrics listener:

```bash
uvicorn openMetricsMicroservice.app:app \
  --app-dir TMF623/source/SLAManagement \
  --port 4000 --reload
```

Tests:

```bash
python3 -m unittest discover -s TMF623/source/SLAManagement/tests -v
```

This is a reference baseline, not a full TMF623 certification target. The implementation focuses on:
- the classic TMF623 `v2` CRUD path surface for `sla`, `slaViolation`, and `hub`
- spec-aligned `PUT` and `PATCH` behavior, including state-change and delete events
- listener registration and callback endpoints
- a simple deterministic data model that is easy to run locally and inside the chart
