# TMF621 Trouble Ticket Management Helm Chart

This chart packages a reference-style implementation of a `TMF621 Trouble Ticket Management` component, following the same broad structure used by the TM Forum sample component repo.

The chart deploys:
- the `TMF621 Trouble Ticket` API
- a small trouble-ticket engine service
- an MCP wrapper over the TMF621 API, enabled by default
- a Party Role API and role bootstrap job
- a metrics listener that subscribes to TMF621 trouble-ticket events
- MongoDB for persistence

Install:

```bash
helm upgrade --install tt1 ./charts/TroubleTicketManagement -n components
```

Base API path:

```text
/<release>-troubleticketmanagement/tmf-api/troubleTicket/v5
```

Example:

```text
/tt1-troubleticketmanagement/tmf-api/troubleTicket/v5
```

Disable the MCP server:

```bash
helm upgrade --install tt1 ./charts/TroubleTicketManagement \
  -n components \
  --set component.MCPServer.enabled=false
```

By default, the chart advertises the normal Streamable HTTP MCP endpoint at `/<release>-troubleticketmanagement/mcp`. That endpoint also keeps legacy SSE compatibility for clients or proxies that open it with `GET`; the SSE message channel is `/<release>-troubleticketmanagement/mcp/messages/`, which path aliases may rewrite for public URLs. Direct in-container `/mcp` and `/sse` routes are available for service-level checks.

Implementation notes:
- The sample API supports `troubleTicket` and `troubleTicketSpecification`.
- Both resources expose list/create/get/patch/delete operations.
- `hub` registration, retrieval, deletion, and listener callback endpoints are included.
