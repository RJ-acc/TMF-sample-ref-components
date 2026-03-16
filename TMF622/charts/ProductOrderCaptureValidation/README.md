# Example Product Order Capture & Validation component

This chart packages a reference-style implementation of a `TMFC002 Product Order Capture & Validation` component, following the same broad structure used by the TM Forum `ProductCatalog` example component.

## Functionality

### Core function

The component exposes:

- the `TMF622 Product Ordering Management` API
- an optional MCP wrapper over the TMF622 API

The component can also declare a dependency on `TMF620 Product Catalog Management`, which is useful when validation logic needs to verify product offerings against a catalog.

### Internal support services

The chart also deploys:

- a dedicated order validation microservice
- a metrics listener that subscribes to order events and exposes Prometheus metrics
- a Party Role API for the security function
- a MongoDB instance used when available by the Python services
- a role initialization job
- a product-order initialization job that registers the metrics listener with the order API

## Installation

```bash
helm install r1 ./charts/ProductOrderCaptureValidation -n components
```

Enable the MCP wrapper:

```bash
helm install r1 ./charts/ProductOrderCaptureValidation \
  --set component.MCPServer.enabled=true \
  -n components
```

When enabled, the chart advertises the MCP endpoint at `/<release>-productordercapturevalidation/mcp` and also keeps the direct in-container `/mcp` route available for service-level checks.

Enable the catalog dependency declaration:

```bash
helm install r1 ./charts/ProductOrderCaptureValidation \
  --set component.dependentAPIs.enabled=true \
  -n components
```

## Notes

- The Python services in this reference are intentionally small and pragmatic.
- The order API captures orders and applies validation rules before moving them into an operational state.
- Validation failures are held with a validation summary so the component demonstrates both capture and validation behavior.
