# TMFC035 Permissions Management Helm Chart

This chart packages a reference-style implementation of a `TMFC035 Permissions Management` component, following the same broad structure used by the TM Forum sample component repo.

The chart deploys:
- the `TMF672 User Role Permission Management` API
- a small permissions-management engine service
- an optional MCP wrapper over the TMF672 API
- a Party Role API and role bootstrap job
- a metrics listener that subscribes to TMF672 permission events
- MongoDB for persistence

Install:

```bash
helm install pm1 ./charts/PermissionsManagement -n components
```

Base API path:

```text
/<release>-permissionsmanagement/tmf-api/rolesAndPermissions/v4
```

Example:

```text
/pm1-permissionsmanagement/tmf-api/rolesAndPermissions/v4
```

Enable the MCP server:

```bash
helm install pm1 ./charts/PermissionsManagement \
  -n components \
  --set component.MCPServer.enabled=true
```

When enabled, the chart advertises the MCP endpoint at `/<release>-permissionsmanagement/mcp` and also keeps the direct in-container `/mcp` route available for service-level checks.

Implementation notes:
- The TMF672 API implements the complete current `v4.0.0` path surface from the official spec.
- Both TMF672 resources support list/create/get/patch.
- `hub` registration and all listener callback endpoints are included.
- Delete operations are intentionally not exposed because TMF672 does not define them.
