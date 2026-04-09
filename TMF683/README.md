# TMFC023 Party Interaction Management

This folder contains a reference-style `TMFC023` component scaffold built around `TMF683 Party Interaction v5.0.0`.

The structure mirrors the pattern used for the other components in this repo:
- a Helm chart under `charts/PartyInteractionManagement`
- a source tree under `source/PartyInteractionManagement`
- a TMF683-based core API for `partyInteraction`
- a metrics listener, role bootstrap job, Party Role API, and optional MCP wrapper

Notes:
- `TMFC023` is modeled around `TMF683 Party Interaction`
- all official TMF683 paths in the current `v5.0.0` OAS are implemented
- the component exposes list, create, retrieve, patch, and delete for `partyInteraction`

Start with:
- `charts/PartyInteractionManagement/README.md`
- `source/PartyInteractionManagement/README.md`
