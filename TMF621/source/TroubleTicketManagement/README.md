# TMF621 Trouble Ticket Management Source

This source tree follows the same reference-component layout used elsewhere in this repo, but implements a Python-based `TMF621 Trouble Ticket Management` baseline for `TMF621 Trouble Ticket v5.0.1`.

Key folders:
- `troubleTicketManagementMicroservice/implementation`
  The core TMF621 API exposing CRUD for `troubleTicket` and `troubleTicketSpecification`, plus `hub` and listener callbacks.
- `troubleTicketManagementEngineMicroservice/implementation`
  A lightweight validation and seed-data service used by the API as an optional helper.
- `common`
  Shared TMF621 resource metadata, seed documents, validation logic, storage helpers, and event utilities.
- `openMetricsMicroservice`
  Prometheus-text metrics listener for TMF621 trouble-ticket events.
- `partyRoleMicroservice`
  Small TMF669 Party Role API used to bootstrap the component system role.
- `troubleTicketManagementInitializationMicroservice/implementation`
  Registers the metrics listener through the TMF621 `hub` endpoint.
- `MCPServerMicroservice`
  Optional MCP wrapper over the TMF621 API.

Local development:

```bash
pip install -r TMF621/source/TroubleTicketManagement/requirements.txt
```

Run the engine:

```bash
uvicorn troubleTicketManagementEngineMicroservice.implementation.app:app \
  --app-dir TMF621/source/TroubleTicketManagement \
  --port 8081 --reload
```

Run the API:

```bash
uvicorn troubleTicketManagementMicroservice.implementation.app:app \
  --app-dir TMF621/source/TroubleTicketManagement \
  --port 8080 --reload
```

Run the Party Role API:

```bash
uvicorn partyRoleMicroservice.implementation.app:app \
  --app-dir TMF621/source/TroubleTicketManagement \
  --port 8090 --reload
```

Run the metrics listener:

```bash
uvicorn openMetricsMicroservice.app:app \
  --app-dir TMF621/source/TroubleTicketManagement \
  --port 4000 --reload
```

Tests:

```bash
python3 -m unittest discover -s TMF621/source/TroubleTicketManagement/tests -v
```

This is a reference baseline, not a full TMF621 certification target. The implementation focuses on:
- spec-aligned CRUD behavior for `troubleTicket` and `troubleTicketSpecification`
- listener registration, retrieval, deletion, and callback endpoints
- deterministic seed data that is easy to run locally and inside the chart
- packaging that matches the other sample components in this repository
