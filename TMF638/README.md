# TMFC008 Service Inventory Management

This folder contains a reference-style `TMFC008` component scaffold built around `TMF638 Service Inventory v5.0.0`.

The structure mirrors the pattern used for the other components in this repo:
- a Helm chart under `charts/ServiceInventoryManagement`
- a source tree under `source/ServiceInventoryManagement`
- a TMF638-based core API for `service`
- a metrics listener, role bootstrap job, Party Role API, and optional MCP wrapper

Notes:
- `TMFC008` is modeled around `TMF638 Service Inventory`
- all official TMF638 paths in the current `v5.0.0` OAS are implemented
- the component exposes list, create, retrieve, patch, and delete for `service`

Start with:
- `charts/ServiceInventoryManagement/README.md`
- `source/ServiceInventoryManagement/README.md`
