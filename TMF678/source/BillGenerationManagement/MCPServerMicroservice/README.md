# TMFC030 Bill Generation Management MCP Server

This optional microservice exposes the TMF678 Customer Bill Management API as MCP tools.

It is intentionally lighter than the broader MCP examples in the upstream sample repo:

- TMF678 tools are generated from the official spec
- listener callback paths are excluded from tool generation
- custom helper tools are included for payload validation and local bill-generation previews

## Local run

Install the optional MCP dependency first:

```bash
pip install -r ../requirements.txt "mcp>=1.0,<2"
```

Then run:

```bash
cd TMF678/source/BillGenerationManagement/MCPServerMicroservice
python server.py --transport http --host 0.0.0.0 --port 8080
```

Relevant environment variables:

- `TMF678_MODE=live|mock`
- `TMF678_BASE_URL=http://localhost:8080`
- `TMF678_API_VERSION=v5`
- `TMF678_SPEC_URL=<spec url>`
- `MCP_HTTP_BASE_PATH=/r1-billgenerationmanagement` to expose the server under a release-prefixed path as well as the default `/mcp`
