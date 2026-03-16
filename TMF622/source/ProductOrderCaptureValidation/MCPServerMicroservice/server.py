from __future__ import annotations

import asyncio
import json
import logging
import sys

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from common.validation import validate_cancel_product_order, validate_product_order
from config import config
from http_executor import execute_tool
from mock_executor import mock_execute
from spec_loader import load_spec
from tool_generator import generate_tools

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("tmf622-mcp")

server = Server(config.SERVER_NAME)
_tool_registry: dict[str, dict] = {}

CUSTOM_TOOLS = [
    types.Tool(
        name="list_all_tools",
        description="List all generated TMF622 MCP tools available on this server.",
        inputSchema={"type": "object", "properties": {}},
    ),
    types.Tool(
        name="validate_product_order_payload",
        description="Validate a TMF622 ProductOrder payload using the TMFC002 validation rules.",
        inputSchema={
            "type": "object",
            "required": ["payload"],
            "properties": {"payload": {"type": "object"}},
        },
    ),
    types.Tool(
        name="validate_cancel_product_order_payload",
        description="Validate a TMF622 CancelProductOrder payload using the TMFC002 validation rules.",
        inputSchema={
            "type": "object",
            "required": ["payload"],
            "properties": {
                "payload": {"type": "object"},
                "product_order_exists": {"type": "boolean"},
            },
        },
    ),
]


async def _ensure_registry() -> None:
    global _tool_registry
    if not _tool_registry:
        spec = await load_spec()
        _tool_registry = generate_tools(spec)


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    await _ensure_registry()
    return [meta["tool"] for meta in _tool_registry.values()] + CUSTOM_TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    await _ensure_registry()
    args = arguments or {}

    if name == "list_all_tools":
        payload = {
            "toolCount": len(_tool_registry),
            "tools": [
                {
                    "name": tool_name,
                    "method": meta["method"].upper(),
                    "path": meta["path"],
                }
                for tool_name, meta in sorted(_tool_registry.items())
            ],
        }
        return [types.TextContent(type="text", text=json.dumps(payload, indent=2))]

    if name == "validate_product_order_payload":
        payload = validate_product_order(args.get("payload", {}))
        return [types.TextContent(type="text", text=json.dumps(payload, indent=2))]

    if name == "validate_cancel_product_order_payload":
        payload = validate_cancel_product_order(
            args.get("payload", {}),
            product_order_exists=args.get("product_order_exists"),
        )
        return [types.TextContent(type="text", text=json.dumps(payload, indent=2))]

    if name not in _tool_registry:
        payload = {"success": False, "error": f"Unknown tool '{name}'"}
        return [types.TextContent(type="text", text=json.dumps(payload, indent=2))]

    tool_meta = _tool_registry[name]
    if config.MODE == "live":
        payload = await execute_tool(tool_meta["path"], tool_meta["method"], tool_meta["parameters"], args)
    else:
        payload = mock_execute(tool_meta["path"], tool_meta["method"], args)

    payload["tool"] = name
    return [types.TextContent(type="text", text=json.dumps(payload, indent=2))]


async def _run_stdio() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


async def _run_http(host: str, port: int) -> None:
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import PlainTextResponse
    from starlette.routing import Mount, Route
    import uvicorn

    def build_sse_routes(mcp_path: str, message_path: str) -> list[Route | Mount]:
        sse_transport = SseServerTransport(message_path)

        async def handle_mcp(request: Request) -> None:
            async with sse_transport.connect_sse(request.scope, request.receive, request._send) as streams:
                await server.run(streams[0], streams[1], server.create_initialization_options())

        return [
            Route(mcp_path, endpoint=handle_mcp),
            Mount(message_path, app=sse_transport.handle_post_message),
        ]

    async def health_check(request: Request) -> PlainTextResponse:
        return PlainTextResponse("OK")

    routes: list[Route | Mount] = build_sse_routes(config.mcp_path, config.mcp_messages_path)

    if config.mcp_path != "/mcp":
        routes.extend(build_sse_routes("/mcp", "/mcp/messages/"))
        routes.append(Route(f"{config.http_base_path}/health", endpoint=health_check))

    routes.append(Route("/health", endpoint=health_check))

    app = Starlette(routes=routes)

    uvicorn_config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    uvicorn_server = uvicorn.Server(uvicorn_config)
    await uvicorn_server.serve()


async def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=f"{config.SERVER_NAME} MCP server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    await _ensure_registry()
    if args.transport == "http":
        await _run_http(args.host, args.port)
    else:
        await _run_stdio()


if __name__ == "__main__":
    asyncio.run(main())
