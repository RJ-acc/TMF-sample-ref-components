# TMFC002 Product Order MCP Server

This optional microservice exposes the TMF622 Product Ordering API as MCP tools.

It is intentionally lighter than the ProductCatalog MCP implementation in the upstream reference repo:

- TMF622 CRUD tools are generated from the official spec
- listener callback paths are excluded from tool generation
- two custom validation tools are included for product order and cancel-order payloads

## Local run

```bash
cd source/ProductOrderCaptureValidation/MCPServerMicroservice
python server.py --transport http --host 0.0.0.0 --port 8080
```

Relevant environment variables:

- `TMF622_MODE=live|mock`
- `TMF622_BASE_URL=http://localhost:8080`
- `TMF622_API_VERSION=v4`
- `TMF622_SPEC_URL=<spec url>`
- `MCP_HTTP_BASE_PATH=/r1-productordercapturevalidation` to expose the server under a release-prefixed path as well as the default `/mcp`
