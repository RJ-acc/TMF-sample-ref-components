# TMFC050 Product Recommendation MCP Server

This optional microservice exposes the TMF680 Recommendation API as MCP tools.

It is intentionally lighter than the ProductCatalog MCP implementation in the upstream reference repo:

- TMF680 tools are generated from the official spec
- listener callback paths are excluded from tool generation
- two custom helper tools are included for payload validation and local recommendation preview

## Local run

Install the optional MCP dependency first:

```bash
pip install "mcp>=1.0,<2"
```

Then run:

```bash
cd TMF680/source/ProductRecommendation/MCPServerMicroservice
python server.py --transport http --host 0.0.0.0 --port 8080
```

Relevant environment variables:

- `TMF680_MODE=live|mock`
- `TMF680_BASE_URL=http://localhost:8080`
- `TMF680_API_VERSION=v4`
- `TMF680_SPEC_URL=<spec url>`
- `MCP_HTTP_BASE_PATH=/r1-productrecommendation` to expose the server under a release-prefixed path as well as the default routes

HTTP endpoints:
- Streamable HTTP: `/mcp` and, when `MCP_HTTP_BASE_PATH` is set, `<base>/mcp`
- Legacy SSE compatibility: `/sse` with POST messages at `/messages/`, and `<base>/sse` with POST messages at `<base>/messages/`
- Compatibility for older aliases: a GET to `/mcp` or `<base>/mcp` without an MCP session header still opens the legacy SSE stream, with POST messages at `/mcp/messages/` or `<base>/mcp/messages/`
