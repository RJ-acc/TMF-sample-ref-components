# TMFC008 Service Inventory Management MCP Server

This optional microservice exposes the TMF638 Service Inventory Management API as MCP tools.

Features:
- TMF638 tools are generated from the official spec
- tools can run in live HTTP mode or mock mode
- custom helper tools validate create and patch payloads for the TMFC008 reference implementation
- the normal remote MCP endpoint is Streamable HTTP at `/mcp`

Run locally:

```bash
cd TMF638/source/ServiceInventoryManagement/MCPServerMicroservice
python server.py --transport http --host 0.0.0.0 --port 8080
```

Environment:
- `TMF638_MODE=live|mock`
- `TMF638_BASE_URL=http://localhost:8080`
- `TMF638_API_VERSION=v5`
- `TMF638_SPEC_URL=<spec url>`
- `MCP_HTTP_BASE_PATH=/r1-serviceinventorymanagement` to expose the server under a release-prefixed path as well as the default routes

HTTP endpoints:
- Streamable HTTP: `/mcp` and, when `MCP_HTTP_BASE_PATH` is set, `<base>/mcp`
- Legacy SSE compatibility: `/sse` with POST messages at `/messages/`, and `<base>/sse` with POST messages at `<base>/messages/`
- Compatibility for older aliases: a GET to `/mcp` or `<base>/mcp` without an MCP session header still opens the legacy SSE stream, with POST messages at `/mcp/messages/` or `<base>/mcp/messages/`
