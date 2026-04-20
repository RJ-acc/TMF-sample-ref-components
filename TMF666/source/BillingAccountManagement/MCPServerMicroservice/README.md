# TMFC024 Billing Account Management MCP Server

This optional microservice exposes the TMF666 Account Management API as MCP tools.

Highlights:
- TMF666 tools are generated from the official spec
- the server can run in `live` mode against the local API or `mock` mode without dependencies
- custom helper tools validate create and patch payloads for the TMFC024 reference implementation

Local usage:

```bash
cd TMF666/source/BillingAccountManagement/MCPServerMicroservice
python server.py --transport stdio
```

Important environment variables:
- `TMF666_MODE=live|mock`
- `TMF666_BASE_URL=http://localhost:8080`
- `TMF666_API_VERSION=v5`
- `TMF666_SPEC_URL=<spec url>`
- `MCP_HTTP_BASE_PATH=/r1-billingaccountmanagement` to expose the server under a release-prefixed path as well as the default routes

HTTP endpoints:
- Streamable HTTP: `/mcp` and, when `MCP_HTTP_BASE_PATH` is set, `<base>/mcp`
- Legacy SSE compatibility: `/sse` with POST messages at `/messages/`, and `<base>/sse` with POST messages at `<base>/messages/`
- Compatibility for older aliases: a GET to `/mcp` or `<base>/mcp` without an MCP session header still opens the legacy SSE stream, with POST messages at `/mcp/messages/` or `<base>/mcp/messages/`
