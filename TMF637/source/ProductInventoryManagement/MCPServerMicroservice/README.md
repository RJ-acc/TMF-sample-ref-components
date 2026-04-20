# TMFC005 Product Inventory Management MCP Server

This optional microservice exposes the TMF637 Product Inventory Management API as MCP tools.

Features:
- TMF637 tools are generated from the official spec
- tools can run in live HTTP mode or mock mode
- custom helper tools validate create and patch payloads for the TMFC005 reference implementation

Run locally:

```bash
cd TMF637/source/ProductInventoryManagement/MCPServerMicroservice
python server.py --transport http --host 0.0.0.0 --port 8080
```

Environment:
- `TMF637_MODE=live|mock`
- `TMF637_BASE_URL=http://localhost:8080`
- `TMF637_API_VERSION=v5`
- `TMF637_SPEC_URL=<spec url>`
- `MCP_HTTP_BASE_PATH=/r1-productinventorymanagement` to expose the server under a release-prefixed path as well as the default routes

HTTP endpoints:
- Streamable HTTP: `/mcp` and, when `MCP_HTTP_BASE_PATH` is set, `<base>/mcp`
- Legacy SSE compatibility: `/sse` with POST messages at `/messages/`, and `<base>/sse` with POST messages at `<base>/messages/`
- Compatibility for older aliases: a GET to `/mcp` or `<base>/mcp` without an MCP session header still opens the legacy SSE stream, with POST messages at `/mcp/messages/` or `<base>/mcp/messages/`
