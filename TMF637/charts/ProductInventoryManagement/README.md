# TMFC005 Product Inventory Management Helm Chart

This chart packages a reference-style implementation of a `TMFC005 Product Inventory Management` component, following the same broad structure used by the TM Forum sample component repo.

The chart deploys:
- the `TMF637 Product Inventory` API
- a product-inventory engine service
- an optional MCP wrapper over the TMF637 API
- a Party Role API and role bootstrap job
- a metrics listener that subscribes to TMF637 product-inventory events
- MongoDB for persistence

Install:

```bash
helm install pi1 ./charts/ProductInventoryManagement -n components
```

Base API path:

```text
/<release>-productinventorymanagement/tmf-api/productInventoryManagement/v5
```

Example:

```text
/pi1-productinventorymanagement/tmf-api/productInventoryManagement/v5
```

Enable the MCP server:

```bash
helm install pi1 ./charts/ProductInventoryManagement \
  -n components \
  --set component.MCPServer.enabled=true
```

When enabled, the chart advertises the MCP endpoint at `/<release>-productinventorymanagement/mcp` and also keeps the direct in-container `/mcp` route available for service-level checks.

Implementation notes:
- The TMF637 API implements the complete current `v5.0.0` path surface from the official spec.
- The `product` resource supports list/create/get/patch/delete.
- `hub` registration and all listener callback endpoints are included.
