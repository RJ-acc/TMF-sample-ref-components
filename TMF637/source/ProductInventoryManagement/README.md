# TMFC005 Product Inventory Management Source

This source tree follows the same reference-component layout used elsewhere in this repo, but implements a Python-based `TMFC005 Product Inventory Management` baseline for `TMF637 Product Inventory v5.0.0`.

Key folders:
- `productInventoryManagementMicroservice/implementation`
  The core TMF637 API exposing CRUD for `product`, plus `hub` and listener callbacks.
- `productInventoryManagementEngineMicroservice/implementation`
  A lightweight validation and seed-data service used by the API as an optional helper.
- `common`
  Shared TMF637 resource metadata, seed documents, validation logic, storage helpers, and event utilities.
- `openMetricsMicroservice`
  Prometheus-text metrics listener for TMF637 product-inventory events.
- `partyRoleMicroservice`
  Small TMF669 Party Role API used to bootstrap the component system role.
- `productInventoryManagementInitializationMicroservice/implementation`
  Registers the metrics listener through the TMF637 `hub` endpoint.
- `MCPServerMicroservice`
  Optional MCP wrapper over the TMF637 API.

Local development:

```bash
pip install -r TMF637/source/ProductInventoryManagement/requirements.txt
```

Run the engine:

```bash
uvicorn productInventoryManagementEngineMicroservice.implementation.app:app \
  --app-dir TMF637/source/ProductInventoryManagement \
  --port 8081 --reload
```

Run the API:

```bash
uvicorn productInventoryManagementMicroservice.implementation.app:app \
  --app-dir TMF637/source/ProductInventoryManagement \
  --port 8080 --reload
```

Run the Party Role API:

```bash
uvicorn partyRoleMicroservice.implementation.app:app \
  --app-dir TMF637/source/ProductInventoryManagement \
  --port 8090 --reload
```

Run the metrics listener:

```bash
uvicorn openMetricsMicroservice.app:app \
  --app-dir TMF637/source/ProductInventoryManagement \
  --port 4000 --reload
```

Tests:

```bash
python3 -m unittest discover -s TMF637/source/ProductInventoryManagement/tests -v
```

This is a reference baseline, not a full TMF637 certification target. The implementation focuses on:
- the complete official TMF637 path surface
- spec-aligned CRUD behavior for `product`
- listener registration and callback endpoints
- a simple deterministic data model that is easy to run locally and inside the chart
