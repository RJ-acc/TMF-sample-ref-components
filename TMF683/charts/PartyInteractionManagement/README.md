# TMFC023 Party Interaction Management Helm Chart

This chart packages a reference-style implementation of a `TMFC023 Party Interaction Management` component, following the same broad structure used by the TM Forum sample component repo.

The chart deploys:
- the `TMF683 Party Interaction` API
- a small interaction-management engine service
- an MCP wrapper over the TMF683 API, enabled by default
- a Party Role API and role bootstrap job
- a metrics listener that subscribes to TMF683 party-interaction events
- MongoDB for persistence

Install:

```bash
helm upgrade --install pi1 ./charts/PartyInteractionManagement -n components
```

Base API path:

```text
/<release>-partyinteractionmanagement/tmf-api/partyInteractionManagement/v5
```

Example:

```text
/pi1-partyinteractionmanagement/tmf-api/partyInteractionManagement/v5
```

Disable the MCP server:

```bash
helm upgrade --install pi1 ./charts/PartyInteractionManagement \
  -n components \
  --set component.MCPServer.enabled=false
```

By default, the chart advertises the MCP endpoint at `/<release>-partyinteractionmanagement/mcp` and also keeps the direct in-container `/mcp` route available for service-level checks.

Implementation notes:
- The TMF683 API implements the complete current `v5.0.0` path surface from the official spec.
- The `partyInteraction` resource supports list/create/get/patch/delete.
- `hub` registration and all listener callback endpoints are included.
