# TMFC027 Product Configurator MCP Server

This optional microservice exposes the TMF760 Product Configuration Management API as MCP tools.

It is intentionally lighter than the ProductCatalog MCP implementation in the upstream reference repo:

- TMF760 tools are generated from the official spec
- listener callback paths are excluded from tool generation
- custom helper tools are included for payload validation and local query/check previews

## Local run

Install the optional MCP dependency first:

```bash
pip install -r ../requirements.txt "mcp>=1.0,<2"
```

Then run:

```bash
cd TMF760/source/ProductConfigurator/MCPServerMicroservice
python server.py --transport http --host 0.0.0.0 --port 8080
```

Relevant environment variables:

- `TMF760_MODE=live|mock`
- `TMF760_BASE_URL=http://localhost:8080`
- `TMF760_API_VERSION=v5`
- `TMF760_SPEC_URL=<spec url>`
- `MCP_HTTP_BASE_PATH=/r1-productconfigurator` to expose the server under a release-prefixed path as well as the default routes

HTTP endpoints:
- Streamable HTTP: `/mcp` and, when `MCP_HTTP_BASE_PATH` is set, `<base>/mcp`
- Legacy SSE compatibility: `/sse` with POST messages at `/messages/`, and `<base>/sse` with POST messages at `<base>/messages/`
- Compatibility for older aliases: a GET to `/mcp` or `<base>/mcp` without an MCP session header still opens the legacy SSE stream, with POST messages at `/mcp/messages/` or `<base>/mcp/messages/`
