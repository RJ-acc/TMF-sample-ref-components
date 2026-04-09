# TMFC001 Product Catalog Management

This folder contains a reference-style `TMFC001` component scaffold built around `TMF620 Product Catalog Management v5.0.0`.

The structure mirrors the pattern used for the other components in this repo:
- a Helm chart under `charts/ProductCatalogManagement`
- a source tree under `source/ProductCatalogManagement`
- a TMF620-based core API for product catalogs, categories, product offerings, prices, specifications, and import/export jobs
- a metrics listener, role bootstrap job, Party Role API, and optional MCP wrapper

Notes:
- `TMFC001` is modeled around `TMF620 Product Catalog Management`
- all official TMF620 paths in the current `v5.0.0` OAS are implemented
- unsupported method combinations are intentionally left to return `405`

Start with:
- `charts/ProductCatalogManagement/README.md`
- `source/ProductCatalogManagement/README.md`
