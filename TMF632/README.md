# TMFC028 Party Management

This folder contains a reference-style `TMFC028` component scaffold built around `TMF632 Party Management v5.0.0`.

The structure mirrors the pattern used for the other components in this repo:
- a Helm chart under `charts/PartyManagement`
- a source tree under `source/PartyManagement`
- a TMF632-based core API for `individual` and `organization`
- a metrics listener, role bootstrap job, Party Role API, and optional MCP wrapper

Notes:
- `TMFC028` is modeled around `TMF632 Party Management`
- all official TMF632 paths in the current `v5.0.0` OAS are implemented
- unsupported method combinations are intentionally left to return `405`

Start with:
- `charts/PartyManagement/README.md`
- `source/PartyManagement/README.md`
