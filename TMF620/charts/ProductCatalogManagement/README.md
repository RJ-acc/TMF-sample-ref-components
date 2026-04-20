# TMFC001 Product Catalog Management Helm Chart

This chart packages a reference-style implementation of a `TMFC001 Product Catalog Management` component, following the same broad structure used by the TM Forum sample component repo.

The chart deploys:
- the `TMF620 Product Catalog Management` API
- an MCP wrapper over the TMF620 API, enabled by default
- a Party Role API and role bootstrap job
- a metrics listener that subscribes to TMF620 catalog-management events
- MongoDB for persistence

Install:

```bash
helm upgrade --install pc1 ./charts/ProductCatalogManagement -n components
```

Base API path:

```text
/<release>-productcatalogmanagement/tmf-api/productCatalogManagement/v4
```

Example:

```text
/pc1-productcatalogmanagement/tmf-api/productCatalogManagement/v4
```

Disable the MCP server:

```bash
helm upgrade --install pc1 ./charts/ProductCatalogManagement \
  -n components \
  --set component.MCPServer.enabled=false
```

By default, the chart advertises the normal Streamable HTTP MCP endpoint at `/<release>-productcatalogmanagement/mcp`. That endpoint also keeps legacy SSE compatibility for clients or proxies that open it with `GET`; the SSE message channel is `/<release>-productcatalogmanagement/mcp/messages/`, which path aliases may rewrite for public URLs. Direct in-container `/mcp` and `/sse` routes are available for service-level checks.

Implementation notes:
- The TMF620 API uses the legacy ProductCatalog sample implementation and exposes the `v4` API path surface.
- `productCatalog`, `category`, `productOffering`, `productOfferingPrice`, and `productSpecification` support list/create/get/patch/delete.
- `importJob` and `exportJob` support list/create/get/delete, matching the official TMF620 task-resource surface.
- `hub` registration and all listener callback endpoints are included.
