# TMFC024 Billing Account Management Helm Chart

This chart packages a reference-style implementation of a `TMFC024 Billing Account Management` component, following the same broad structure used by the TM Forum sample component repo.

The chart deploys:
- the `TMF666 Account Management` API
- a small account-management engine service
- an optional MCP wrapper over the TMF666 API
- a Party Role API and role bootstrap job
- a metrics listener that subscribes to TMF666 account-management events
- MongoDB for persistence

Install:

```bash
helm install ba1 ./charts/BillingAccountManagement -n components
```

Base API path:

```text
/<release>-billingaccountmanagement/tmf-api/accountManagement/v5
```

Example:

```text
/ba1-billingaccountmanagement/tmf-api/accountManagement/v5
```

Enable the MCP server:

```bash
helm install ba1 ./charts/BillingAccountManagement \
  -n components \
  --set component.MCPServer.enabled=true
```

When enabled, the chart advertises the MCP endpoint at `/<release>-billingaccountmanagement/mcp` and also keeps the direct in-container `/mcp` route available for service-level checks.

Implementation notes:
- The TMF666 API implements the complete current `v5.0.0` path surface from the official spec.
- All seven TMF666 account resources support list/create/get/patch/delete.
- `hub` registration and all listener callback endpoints are included.
