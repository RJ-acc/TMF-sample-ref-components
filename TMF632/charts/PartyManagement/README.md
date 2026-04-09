# TMFC028 Party Management Helm Chart

This chart packages a reference-style implementation of a `TMFC028 Party Management` component, following the same broad structure used by the TM Forum sample component repo.

The chart deploys:
- the `TMF632 Party Management` API
- a small party-management engine service
- an optional MCP wrapper over the TMF632 API
- a Party Role API and role bootstrap job
- a metrics listener that subscribes to TMF632 party-management events
- MongoDB for persistence

Install:

```bash
helm install pm1 ./charts/PartyManagement -n components
```

Base API path:

```text
/<release>-partymanagement/tmf-api/partyManagement/v5
```

Example:

```text
/pm1-partymanagement/tmf-api/partyManagement/v5
```

Enable the MCP server:

```bash
helm install pm1 ./charts/PartyManagement \
  -n components \
  --set component.MCPServer.enabled=true
```

When enabled, the chart advertises the MCP endpoint at `/<release>-partymanagement/mcp` and also keeps the direct in-container `/mcp` route available for service-level checks.

Implementation notes:
- The TMF632 API implements the complete current `v5.0.0` path surface from the official spec.
- Both TMF632 party resources support list/create/get/patch/delete.
- `hub` registration and all listener callback endpoints are included.
