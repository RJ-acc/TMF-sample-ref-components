# Example Product Recommendation component

This chart packages a reference-style implementation of a `TMFC050 Product Recommendation` component, following the same broad structure used by the TM Forum sample component repo.

## Functionality

### Core function

The component exposes:

- the `TMF680 Recommendation` API
- an MCP wrapper over the TMF680 API, enabled by default

The component can also declare a dependency on `TMF620 Product Catalog Management`, which is useful when recommendation ranking needs product-offering context.

### Internal support services

The chart also deploys:

- a dedicated recommendation engine microservice
- a metrics listener that subscribes to recommendation events and exposes Prometheus-format metrics
- a Party Role API for the security function
- a MongoDB instance used when available by the Python services
- a role initialization job
- a product-recommendation initialization job that registers the metrics listener with the recommendation API

## Installation

```bash
helm upgrade --install r1 ./charts/ProductRecommendation -n components
```

Disable the MCP wrapper:

```bash
helm upgrade --install r1 ./charts/ProductRecommendation \
  --set component.MCPServer.enabled=false \
  -n components
```

By default, the chart advertises the MCP endpoint at `/<release>-productrecommendation/mcp` and also keeps the direct in-container `/mcp` route available for service-level checks.

Enable the catalog dependency declaration:

```bash
helm upgrade --install r1 ./charts/ProductRecommendation \
  --set component.dependentAPIs.enabled=true \
  -n components
```

## Notes

- The Python services in this reference are intentionally small and pragmatic.
- The recommendation API implements the spec-defined `list`, `create`, and `retrieve` operations for `queryProductRecommendation`.
- `TMF680` does not define `patch` or `delete` for `queryProductRecommendation`, so those methods are intentionally not exposed.
