# TMFC005 Product Inventory Management

This folder contains a reference-style `TMFC005` component scaffold built around `TMF637 Product Inventory v5.0.0`.

The structure mirrors the pattern used for the other components in this repo:
- a Helm chart under `charts/ProductInventoryManagement`
- a source tree under `source/ProductInventoryManagement`
- a TMF637-based core API for `product`
- a metrics listener, role bootstrap job, Party Role API, and optional MCP wrapper

Notes:
- `TMFC005` is modeled around `TMF637 Product Inventory`
- all official TMF637 paths in the current `v5.0.0` OAS are implemented
- the component exposes list, create, retrieve, patch, and delete for `product`

Start with:
- `charts/ProductInventoryManagement/README.md`
- `source/ProductInventoryManagement/README.md`
