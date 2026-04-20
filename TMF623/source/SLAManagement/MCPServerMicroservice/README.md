# TMF623 SLA Management MCP Server

This optional microservice exposes the TMF623 SLA Management API as MCP tools.

Features:
- TMF623 tools are generated from the public swagger shape
- tools can run in live HTTP mode or mock mode
- custom helper tools validate create, patch, and replace payloads for the TMF623 reference implementation
- a local `spec_cache/TMF623.json` is bundled so the server can start without fetching the swagger first

Run locally:

```bash
cd TMF623/source/SLAManagement/MCPServerMicroservice
python server.py --transport http --host 0.0.0.0 --port 8080
```

Environment:
- `TMF623_MODE=live|mock`
- `TMF623_BASE_URL=http://localhost:8080`
- `TMF623_API_VERSION=v2`
- `TMF623_SPEC_URL=https://raw.githubusercontent.com/tmforum/TMFAPISWAGGER/develop/slaManagement/v2/swagger2.json`
- `MCP_HTTP_BASE_PATH=/r1-slamanagement` to expose the server under a release-prefixed path as well as the default routes

HTTP endpoints:
- Streamable HTTP: `/mcp` and, when `MCP_HTTP_BASE_PATH` is set, `<base>/mcp`
- Legacy SSE compatibility: `/sse` with POST messages at `/messages/`, and `<base>/sse` with POST messages at `<base>/messages/`
- Compatibility for older aliases: a GET to `/mcp` or `<base>/mcp` without an MCP session header still opens the legacy SSE stream, with POST messages at `/mcp/messages/` or `<base>/mcp/messages/`
