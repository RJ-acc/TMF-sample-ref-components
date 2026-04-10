# TMF623 SLA Management Helm Chart

This chart packages a reference-style implementation of a `TMF623 SLA Management` component, following the same broad structure used by the TM Forum sample component repo.

The chart deploys:
- the `TMF623 SLA Management v2` API
- a small SLA-management engine service
- an MCP wrapper over the TMF623 API, enabled by default
- a Party Role API and role bootstrap job
- a metrics listener that subscribes to TMF623 SLA events
- MongoDB for persistence

Install:

```bash
helm upgrade --install sm1 ./charts/SLAManagement -n components
```

Base API path:

```text
/<release>-slamanagement/tmf-api/slaManagement/v2
```

Example:

```text
/sm1-slamanagement/tmf-api/slaManagement/v2
```

Disable the MCP server:

```bash
helm upgrade --install sm1 ./charts/SLAManagement \
  -n components \
  --set component.MCPServer.enabled=false
```

By default, the chart advertises the MCP endpoint at `/<release>-slamanagement/mcp` and also keeps the direct in-container `/mcp` route available for service-level checks.

Implementation notes:
- The TMF623 API follows the public `slaManagement/v2/swagger2.json` surface.
- Both `sla` and `slaViolation` support list/create/get/delete/put/patch.
- `hub` supports list/create/get/delete, and listener callback endpoints are included.
- Image values default to `ravijangra92/tmf623:*` tags for the published Docker Hub repository used by this repo.
