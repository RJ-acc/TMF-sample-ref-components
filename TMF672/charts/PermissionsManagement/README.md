# TMFC035 Permissions Management Helm Chart

This chart packages a reference-style implementation of a `TMFC035 Permissions Management` component, following the same broad structure used by the TM Forum sample component repo.

The chart deploys:
- the `TMF672 User Role Permission Management` API
- a small permissions-management engine service
- an MCP wrapper over the TMF672 API, enabled by default
- a Party Role API and role bootstrap job
- a metrics listener that subscribes to TMF672 permission events
- MongoDB for persistence

Install:

```bash
helm upgrade --install pe1 ./charts/PermissionsManagement -n components
```

Base API path:

```text
/<release>-permissionsmanagement/tmf-api/rolesAndPermissions/v4
```

Example:

```text
/pe1-permissionsmanagement/tmf-api/rolesAndPermissions/v4
```

Disable the MCP server:

```bash
helm upgrade --install pe1 ./charts/PermissionsManagement \
  -n components \
  --set component.MCPServer.enabled=false
```

By default, the chart advertises the normal Streamable HTTP MCP endpoint at `/<release>-permissionsmanagement/mcp`. That endpoint also keeps legacy SSE compatibility for clients or proxies that open it with `GET`; the SSE message channel is `/<release>-permissionsmanagement/mcp/messages/`, which path aliases may rewrite for public URLs. Direct in-container `/mcp` and `/sse` routes are available for service-level checks.

Implementation notes:
- The TMF672 API implements the complete current `v4.0.0` path surface from the official spec.
- Both TMF672 resources support list/create/get/patch.
- `hub` registration and all listener callback endpoints are included.
- Delete operations are intentionally not exposed because TMF672 does not define them.
