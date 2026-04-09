# TMFC023 Party Interaction Management Source

This source tree follows the same reference-component layout used elsewhere in this repo, but implements a Python-based `TMFC023 Party Interaction Management` baseline for `TMF683 Party Interaction v5.0.0`.

Key folders:
- `partyInteractionManagementMicroservice/implementation`
  The core TMF683 API exposing CRUD for `partyInteraction`, plus `hub` and listener callbacks.
- `partyInteractionManagementEngineMicroservice/implementation`
  A lightweight validation and seed-data service used by the API as an optional helper.
- `common`
  Shared TMF683 resource metadata, seed documents, validation logic, storage helpers, and event utilities.
- `openMetricsMicroservice`
  Prometheus-text metrics listener for TMF683 party-interaction events.
- `partyRoleMicroservice`
  Small TMF669 Party Role API used to bootstrap the component system role.
- `partyInteractionManagementInitializationMicroservice/implementation`
  Registers the metrics listener through the TMF683 `hub` endpoint.
- `MCPServerMicroservice`
  Optional MCP wrapper over the TMF683 API.

Local development:

```bash
pip install -r TMF683/source/PartyInteractionManagement/requirements.txt
```

Run the engine:

```bash
uvicorn partyInteractionManagementEngineMicroservice.implementation.app:app \
  --app-dir TMF683/source/PartyInteractionManagement \
  --port 8081 --reload
```

Run the API:

```bash
uvicorn partyInteractionManagementMicroservice.implementation.app:app \
  --app-dir TMF683/source/PartyInteractionManagement \
  --port 8080 --reload
```

Run the Party Role API:

```bash
uvicorn partyRoleMicroservice.implementation.app:app \
  --app-dir TMF683/source/PartyInteractionManagement \
  --port 8090 --reload
```

Run the metrics listener:

```bash
uvicorn openMetricsMicroservice.app:app \
  --app-dir TMF683/source/PartyInteractionManagement \
  --port 4000 --reload
```

Tests:

```bash
python3 -m unittest discover -s TMF683/source/PartyInteractionManagement/tests -v
```

This is a reference baseline, not a full TMF683 certification target. The implementation focuses on:
- the complete official TMF683 path surface
- spec-aligned CRUD behavior for `partyInteraction`
- listener registration and callback endpoints
- a simple deterministic data model that is easy to run locally and inside the chart
