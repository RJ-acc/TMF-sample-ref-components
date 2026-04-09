# TMFC023 Party Interaction Management MCP Server

This optional microservice exposes the TMF683 Party Interaction Management API as MCP tools.

Features:
- TMF683 tools are generated from the official spec
- tools can run in live HTTP mode or mock mode
- custom helper tools validate create and patch payloads for the TMFC023 reference implementation

Run locally:

```bash
cd TMF683/source/PartyInteractionManagement/MCPServerMicroservice
python server.py --transport http --host 0.0.0.0 --port 8080
```

Environment:
- `TMF683_MODE=live|mock`
- `TMF683_BASE_URL=http://localhost:8080`
- `TMF683_API_VERSION=v5`
- `TMF683_SPEC_URL=<spec url>`
- `MCP_HTTP_BASE_PATH=/r1-partyinteractionmanagement` to expose the server under a release-prefixed path as well as the default `/mcp`
