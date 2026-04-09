# TMFC001 Product Catalog Management MCP Server

This optional microservice exposes the TMF620 Product Catalog Management API as MCP tools.

Highlights:
- TMF620 tools are generated from the official spec
- the server can run in `live` mode against the local API or `mock` mode without dependencies
- custom helper tools validate create and patch payloads for the TMFC001 reference implementation

Local usage:

```bash
cd TMF620/source/ProductCatalogManagement/MCPServerMicroservice
python server.py --transport stdio
```

Important environment variables:
- `TMF620_MODE=live|mock`
- `TMF620_BASE_URL=http://localhost:8080`
- `TMF620_API_VERSION=v5`
- `TMF620_SPEC_URL=<spec url>`
- `MCP_HTTP_BASE_PATH=/r1-productcatalogmanagement` to expose the server under a release-prefixed path as well as the default `/mcp`
