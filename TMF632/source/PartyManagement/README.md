# TMFC028 Party Management Source

This source tree follows the same reference-component layout used elsewhere in this repo, but implements a Python-based `TMFC028 Party Management` baseline for `TMF632 Party Management v5.0.0`.

Key folders:
- `partyManagementMicroservice/implementation`
  The core TMF632 API exposing full CRUD for `individual` and `organization`, plus `hub` and listener callbacks.
- `partyManagementEngineMicroservice/implementation`
  A lightweight validation and seed-data service used by the API as an optional helper.
- `common`
  Shared TMF632 resource metadata, seed documents, validation logic, storage helpers, and event utilities.
- `openMetricsMicroservice`
  Prometheus-text metrics listener for TMF632 party-management events.
- `partyRoleMicroservice`
  Small TMF669 Party Role API used to bootstrap the component system role.
- `partyManagementInitializationMicroservice/implementation`
  Registers the metrics listener through the TMF632 `hub` endpoint.
- `MCPServerMicroservice`
  Optional MCP wrapper over the TMF632 API.

Local development:

```bash
pip install -r TMF632/source/PartyManagement/requirements.txt
```

Run the engine:

```bash
uvicorn partyManagementEngineMicroservice.implementation.app:app \
  --app-dir TMF632/source/PartyManagement \
  --port 8081 --reload
```

Run the API:

```bash
uvicorn partyManagementMicroservice.implementation.app:app \
  --app-dir TMF632/source/PartyManagement \
  --port 8080 --reload
```

Run the Party Role API:

```bash
uvicorn partyRoleMicroservice.implementation.app:app \
  --app-dir TMF632/source/PartyManagement \
  --port 8090 --reload
```

Run the metrics listener:

```bash
uvicorn openMetricsMicroservice.app:app \
  --app-dir TMF632/source/PartyManagement \
  --port 4000 --reload
```

Tests:

```bash
python3 -m unittest discover -s TMF632/source/PartyManagement/tests -v
```

This is a reference baseline, not a full TMF632 certification target. The implementation focuses on:
- the complete official TMF632 path surface
- spec-aligned CRUD behavior for Individuals and Organizations
- listener registration and callback endpoints
- a simple deterministic data model that is easy to run locally and inside the chart
