# TMF623 SLA Management

This folder contains a reference-style `TMF623 SLA Management` component scaffold built around the classic `TMF623 SLA Management v2.0` swagger.

The structure mirrors the pattern used for the other components in this repo:
- a Helm chart under `charts/SLAManagement`
- a source tree under `source/SLAManagement`
- a TMF623-based core API for `sla` and `slaViolation`
- a metrics listener, role bootstrap job, Party Role API, and optional MCP wrapper

Notes:
- `TMF623` is modeled around the `slaManagement/v2/swagger2.json` surface from the TM Forum swagger repository
- both `sla` and `slaViolation` support list, create, retrieve, replace, patch, and delete
- `hub` supports list, create, retrieve, and delete subscription flows

Start with:
- `charts/SLAManagement/README.md`
- `source/SLAManagement/README.md`
