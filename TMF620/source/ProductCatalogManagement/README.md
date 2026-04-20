# TMFC001 Product Catalog Management Source

This source tree uses the legacy `ProductCatalog` sample implementation:

- Node.js TMF620 Product Catalog API
- Node.js Party Role API
- Node.js metrics listener
- Node.js bootstrap jobs
- Python Streamable HTTP MCP server

The Helm chart deploys the TMF620 API at:

```text
/<release>-productcatalogmanagement/tmf-api/productCatalogManagement/v4
```

The MCP server is exposed at:

```text
/<release>-productcatalogmanagement/mcp
```

Image names are kept under `ravijangra92/tmf620:*` to match the chart values. Do not run `builddockerfile.sh` until the target tags are confirmed.
