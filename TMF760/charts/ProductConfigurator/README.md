# Example Product Configurator component

This chart packages a reference-style implementation of a `TMFC027 Product Configurator` component, following the same broad structure used by the TM Forum sample component repo.

## What it deploys

The chart creates a runnable component shape for:

- the `TMF760 Product Configuration Management` API
- an internal configuration engine
- an MCP wrapper over the TMF760 API, enabled by default
- a MongoDB backing store
- a metrics listener that subscribes to TMF760 create/state-change events
- a simplified `TMF669 Party Role Management` API for the security function
- a role initialization job
- a product-configurator initialization job that registers the metrics listener with the API

## Install

```bash
helm upgrade --install pr1 ./charts/ProductConfigurator -n components
```

The public core API base path is exposed as:

```text
/<release>-productconfigurator/tmf-api/productConfiguration/v5
```

Example:

```text
/pr1-productconfigurator/tmf-api/productConfiguration/v5
```

## MCP server

The MCP wrapper is enabled by default. Disable it with:

```bash
helm upgrade --install pr1 ./charts/ProductConfigurator \
  -n components \
  --set component.MCPServer.enabled=false
```

By default, the chart advertises the normal Streamable HTTP MCP endpoint at `/<release>-productconfigurator/mcp`. That endpoint also keeps legacy SSE compatibility for clients or proxies that open it with `GET`; the SSE message channel is `/<release>-productconfigurator/mcp/messages/`, which path aliases may rewrite for public URLs. Direct in-container `/mcp` and `/sse` routes are available for service-level checks.

## Image values

The default values point to placeholder tags under `ravijangra92/tmf760`. Update them before cluster deployment if you publish the images under a different Docker Hub repository.

## Notes

- The product-configuration API implements the spec-defined `list`, `create`, and `retrieve` operations for both `queryProductConfiguration` and `checkProductConfiguration`.
- `TMF760` does not define `patch` or `delete` for these main resources, so those methods are intentionally not exposed.
- The chart uses a single MongoDB instance for the API and the party-role service.
- The configuration engine is internal and not exposed as a NodePort service.
