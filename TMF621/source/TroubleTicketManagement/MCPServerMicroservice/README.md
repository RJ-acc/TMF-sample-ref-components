# TMF621 Trouble Ticket Management MCP Server

This optional microservice exposes the TMF621 Trouble Ticket API as MCP tools.

Features:
- TMF621 tools are generated from the official spec
- tools can run in live HTTP mode or mock mode
- custom helper tools validate and preview `troubleTicket` and `troubleTicketSpecification` payloads

Run locally:

```bash
cd TMF621/source/TroubleTicketManagement/MCPServerMicroservice
python server.py --transport http --host 0.0.0.0 --port 8080
```

Environment:
- `TMF621_MODE=live|mock`
- `TMF621_BASE_URL=http://localhost:8080`
- `TMF621_API_VERSION=v5`
- `TMF621_SPEC_URL=<spec url>`
- `MCP_HTTP_BASE_PATH=/r1-troubleticketmanagement` to expose the server under a release-prefixed path as well as the default routes

HTTP endpoints:
- Streamable HTTP: `/mcp` and, when `MCP_HTTP_BASE_PATH` is set, `<base>/mcp`
- Legacy SSE compatibility: `/sse` with POST messages at `/messages/`, and `<base>/sse` with POST messages at `<base>/messages/`
- Compatibility for older aliases: a GET to `/mcp` or `<base>/mcp` without an MCP session header still opens the legacy SSE stream, with POST messages at `/mcp/messages/` or `<base>/mcp/messages/`
