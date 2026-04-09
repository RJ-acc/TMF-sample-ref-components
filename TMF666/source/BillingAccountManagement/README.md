# TMFC024 Billing Account Management Source

This source tree follows the same reference-component layout used elsewhere in this repo, but implements a Python-based `TMFC024 Billing Account Management` baseline for `TMF666 Account Management v5.0.0`.

Key folders:
- `billingAccountManagementMicroservice/implementation`
  The core TMF666 API exposing full CRUD for the seven account-management resources plus `hub` and listener callbacks.
- `accountManagementEngineMicroservice/implementation`
  A lightweight validation and seed-data service used by the API as an optional helper.
- `common`
  Shared TMF666 resource metadata, seed documents, validation logic, storage helpers, and event utilities.
- `openMetricsMicroservice`
  Prometheus-text metrics listener for TMF666 account-management events.
- `partyRoleMicroservice`
  Small TMF669 Party Role API used to bootstrap the component system role.
- `billingAccountInitializationMicroservice/implementation`
  Registers the metrics listener through the TMF666 `hub` endpoint.
- `MCPServerMicroservice`
  Optional MCP wrapper over the TMF666 API.

Local development:

```bash
pip install -r TMF666/source/BillingAccountManagement/requirements.txt
```

Run the engine:

```bash
uvicorn accountManagementEngineMicroservice.implementation.app:app \
  --app-dir TMF666/source/BillingAccountManagement \
  --port 8081 --reload
```

Run the API:

```bash
uvicorn billingAccountManagementMicroservice.implementation.app:app \
  --app-dir TMF666/source/BillingAccountManagement \
  --port 8080 --reload
```

Run the Party Role API:

```bash
uvicorn partyRoleMicroservice.implementation.app:app \
  --app-dir TMF666/source/BillingAccountManagement \
  --port 8090 --reload
```

Run the metrics listener:

```bash
uvicorn openMetricsMicroservice.app:app \
  --app-dir TMF666/source/BillingAccountManagement \
  --port 4000 --reload
```

Tests:

```bash
python3 -m unittest discover -s TMF666/source/BillingAccountManagement/tests -v
```

This is a reference baseline, not a full TMF666 certification target. The implementation focuses on:
- the complete official TMF666 path surface
- spec-aligned CRUD behavior for all seven resources
- listener registration and callback endpoints
- a simple deterministic data model that is easy to run locally and inside the chart
