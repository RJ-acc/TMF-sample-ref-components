# TMFC001 Product Catalog Management Source

This source tree follows the same reference-component layout used elsewhere in this repo, but implements a Python-based `TMFC001 Product Catalog Management` baseline for `TMF620 Product Catalog Management v5.0.0`.

Key folders:
- `productCatalogManagementMicroservice/implementation`
  The core TMF620 API exposing CRUD for `productCatalog`, `category`, `productOffering`, `productOfferingPrice`, and `productSpecification`, plus task-style `importJob` and `exportJob` operations, `hub`, and listener callbacks.
- `catalogManagementEngineMicroservice/implementation`
  A lightweight validation and seed-data service used by the API as an optional helper.
- `common`
  Shared TMF620 resource metadata, seed documents, validation logic, storage helpers, and event utilities.
- `openMetricsMicroservice`
  Prometheus-text metrics listener for TMF620 catalog-management events.
- `partyRoleMicroservice`
  Small TMF669 Party Role API used to bootstrap the component system role.
- `productCatalogInitializationMicroservice/implementation`
  Registers the metrics listener through the TMF620 `hub` endpoint.
- `MCPServerMicroservice`
  Optional MCP wrapper over the TMF620 API.

Local development:

```bash
pip install -r TMF620/source/ProductCatalogManagement/requirements.txt
```

Run the engine:

```bash
uvicorn catalogManagementEngineMicroservice.implementation.app:app \
  --app-dir TMF620/source/ProductCatalogManagement \
  --port 8081 --reload
```

Run the API:

```bash
uvicorn productCatalogManagementMicroservice.implementation.app:app \
  --app-dir TMF620/source/ProductCatalogManagement \
  --port 8080 --reload
```

Run the Party Role API:

```bash
uvicorn partyRoleMicroservice.implementation.app:app \
  --app-dir TMF620/source/ProductCatalogManagement \
  --port 8090 --reload
```

Run the metrics listener:

```bash
uvicorn openMetricsMicroservice.app:app \
  --app-dir TMF620/source/ProductCatalogManagement \
  --port 4000 --reload
```

Tests:

```bash
python3 -m unittest discover -s TMF620/source/ProductCatalogManagement/tests -v
```

This is a reference baseline, not a full TMF620 certification target. The implementation focuses on:
- the complete official TMF620 path surface
- spec-aligned CRUD behavior for the main catalog resources
- task-resource support for import and export jobs
- listener registration and callback endpoints
- a simple deterministic data model that is easy to run locally and inside the chart
