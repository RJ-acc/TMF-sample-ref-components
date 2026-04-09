# TMFC035 Permissions Management MCP Server

This optional microservice exposes the TMF672 Permissions Management API as MCP tools.

Features:
- TMF672 tools are generated from the official spec
- tools can run in live HTTP mode or mock mode
- custom helper tools validate create and patch payloads for the TMFC035 reference implementation

Run locally:

```bash
cd TMF672/source/PermissionsManagement/MCPServerMicroservice
python server.py --transport http --host 0.0.0.0 --port 8080
```

Environment:
- `TMF672_MODE=live|mock`
- `TMF672_BASE_URL=http://localhost:8080`
- `TMF672_API_VERSION=v4`
- `TMF672_SPEC_URL=<spec url>`
- `MCP_HTTP_BASE_PATH=/r1-permissionsmanagement` to expose the server under a release-prefixed path as well as the default `/mcp`
