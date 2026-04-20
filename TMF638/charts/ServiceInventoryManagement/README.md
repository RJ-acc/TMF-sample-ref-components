# TMFC008 Service Inventory Management Helm Chart

This chart packages a reference-style implementation of a `TMFC008 Service Inventory Management` component, following the same broad structure used by the TM Forum sample component repo.

The chart deploys:
- the `TMF638 Service Inventory` API
- a service-inventory engine service
- an MCP wrapper over the TMF638 API, enabled by default
- a Party Role API and role bootstrap job
- a metrics listener that subscribes to TMF638 service-inventory events
- MongoDB for persistence

Install:

```bash
helm upgrade --install pi1 ./charts/ServiceInventoryManagement -n components
```

Base API path:

```text
/<release>-serviceinventorymanagement/tmf-api/serviceInventoryManagement/v5
```

Example:

```text
/pi1-serviceinventorymanagement/tmf-api/serviceInventoryManagement/v5
```

Disable the MCP server:

```bash
helm upgrade --install pi1 ./charts/ServiceInventoryManagement \
  -n components \
  --set component.MCPServer.enabled=false
```

By default, the chart advertises the normal Streamable HTTP MCP endpoint at `/<release>-serviceinventorymanagement/mcp`. That endpoint also keeps legacy SSE compatibility for clients or proxies that open it with `GET`; the SSE message channel is `/<release>-serviceinventorymanagement/mcp/messages/`, which path aliases may rewrite for public URLs. Direct in-container `/mcp` and `/sse` routes are available for service-level checks.

Implementation notes:
- The TMF638 API implements the complete current `v5.0.0` path surface from the official spec.
- The `service` resource supports list/create/get/patch/delete.
- `hub` registration and all listener callback endpoints are included.
