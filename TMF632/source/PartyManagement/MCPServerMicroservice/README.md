# TMFC028 Party Management MCP Server

This optional microservice exposes the TMF632 Party Management API as MCP tools.

Highlights:
- TMF632 tools are generated from the official spec
- the server can run in `live` mode against the local API or `mock` mode without dependencies
- custom helper tools validate create and patch payloads for the TMFC028 reference implementation

Local usage:

```bash
cd TMF632/source/PartyManagement/MCPServerMicroservice
python server.py --transport stdio
```

Important environment variables:
- `TMF632_MODE=live|mock`
- `TMF632_BASE_URL=http://localhost:8080`
- `TMF632_API_VERSION=v5`
- `TMF632_SPEC_URL=<spec url>`
- `MCP_HTTP_BASE_PATH=/r1-partymanagement` to expose the server under a release-prefixed path as well as the default `/mcp`
