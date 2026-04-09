# Example Bill Generation Management component

This chart packages a reference-style implementation of a `TMFC030 Bill Generation Management` component, following the same broad structure used by the TM Forum sample component repo.

## What it deploys

The chart creates a runnable component shape for:

- the `TMF678 Customer Bill Management` API
- an internal bill-generation engine
- an optional MCP wrapper over the TMF678 API
- a MongoDB backing store
- a metrics listener that subscribes to TMF678 create and state-change events
- a simplified `TMF669 Party Role Management` API for the security function
- a role initialization job
- a bill-generation initialization job that registers the metrics listener with the API

## Install

```bash
helm install pr1 ./charts/BillGenerationManagement -n components
```

The public core API base path is exposed as:

```text
/<release>-billgenerationmanagement/tmf-api/customerBillManagement/v5
```

Example:

```text
/pr1-billgenerationmanagement/tmf-api/customerBillManagement/v5
```

## Optional MCP server

Enable the MCP wrapper:

```bash
helm install pr1 ./charts/BillGenerationManagement \
  -n components \
  --set component.MCPServer.enabled=true
```

When enabled, the chart advertises the MCP endpoint at `/<release>-billgenerationmanagement/mcp` and also keeps the direct in-container `/mcp` route available for service-level checks.

## Image values

The default values point to placeholder tags under `ravijangra92/tmf678`. Update them before cluster deployment if you publish the images under a different Docker Hub repository.

## Notes

- The TMF678 API implements the spec-defined list/get surface for `appliedCustomerBillingRate` and `billCycle`.
- `customerBill` supports list/get/patch exactly as defined by TMF678.
- `customerBillOnDemand` supports list/create/get exactly as defined by TMF678.
- The chart uses a single MongoDB instance for the API and the party-role service.
- The bill-generation engine is internal and not exposed as a NodePort service.
