# TMFC035 Permissions Management

This folder contains a reference-style `TMFC035` component scaffold built around `TMF672 User Role Permission Management v4.0.0`.

The structure mirrors the pattern used for the other components in this repo:
- a Helm chart under `charts/PermissionsManagement`
- a source tree under `source/PermissionsManagement`
- a TMF672-based core API for `permission` and `userRole`
- a metrics listener, role bootstrap job, Party Role API, and optional MCP wrapper

Notes:
- `TMFC035` is modeled around `TMF672 User Role Permission Management`
- the implemented path surface matches the official TMF672 `v4.0.0` swagger
- TMF672 defines list, create, retrieve, and patch operations for `permission` and `userRole`; delete is intentionally left unsupported and returns `405`

Start with:
- `charts/PermissionsManagement/README.md`
- `source/PermissionsManagement/README.md`
