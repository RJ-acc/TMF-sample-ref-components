from __future__ import annotations

import asyncio
import json
import logging
import sys

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from common.recommendations import generate_recommendations
from common.validation import validate_query_product_recommendation
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
logger = logging.getLogger("tmf680-mcp")

server = Server(config.SERVER_NAME)
_tool_registry: dict[str, dict] = {}

CUSTOM_TOOLS = [
    types.Tool(
        name="list_all_tools",
        description="List all generated TMF680 MCP tools available on this server.",
        inputSchema={"type": "object", "properties": {}},
    ),
    types.Tool(
        name="validate_query_product_recommendation_payload",
        description="Validate a TMF680 QueryProductRecommendation payload using the TMFC050 validation rules.",
        inputSchema={
            "type": "object",
            "required": ["payload"],
            "properties": {"payload": {"type": "object"}},
        },
    ),
    types.Tool(
        name="preview_query_product_recommendation_payload",
        description="Generate a local recommendation preview using the TMFC050 starter ranking rules.",
        inputSchema={
            "type": "object",
            "required": ["payload"],
            "properties": {"payload": {"type": "object"}},
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

    if name == "validate_query_product_recommendation_payload":
        payload = validate_query_product_recommendation(args.get("payload", {}))
        return [types.TextContent(type="text", text=json.dumps(payload, indent=2))]

    if name == "preview_query_product_recommendation_payload":
        payload = generate_recommendations(args.get("payload", {}))
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
    from contextlib import asynccontextmanager

    from mcp.server.sse import SseServerTransport
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.middleware.cors import CORSMiddleware
    from starlette.routing import Mount, Route
    import uvicorn

    class StreamableHTTPApp:
        def __init__(self, session_manager: StreamableHTTPSessionManager):
            self.session_manager = session_manager

        async def __call__(self, scope, receive, send) -> None:
            await self.session_manager.handle_request(scope, receive, send)

    class LegacySSEApp:
        def __init__(self, sse_transport: SseServerTransport):
            self.sse_transport = sse_transport

        async def __call__(self, scope, receive, send) -> None:
            async with self.sse_transport.connect_sse(scope, receive, send) as streams:
                await server.run(streams[0], streams[1], server.create_initialization_options())

    class MCPTransportApp:
        def __init__(self, streamable_app: StreamableHTTPApp, sse_app: LegacySSEApp):
            self.streamable_app = streamable_app
            self.sse_app = sse_app

        async def __call__(self, scope, receive, send) -> None:
            headers = dict(scope.get("headers", []))
            is_legacy_sse_open = scope.get("method") == "GET" and b"mcp-session-id" not in headers
            if is_legacy_sse_open:
                await self.sse_app(scope, receive, send)
                return

            await self.streamable_app(scope, receive, send)

    session_manager = StreamableHTTPSessionManager(app=server)
    streamable_app = StreamableHTTPApp(session_manager)

    def build_transport_routes(
        mcp_path: str,
        mcp_message_path: str,
        sse_path: str,
        sse_message_path: str,
    ) -> list[Route | Mount]:
        mcp_sse_transport = SseServerTransport(mcp_message_path)
        mcp_sse_app = LegacySSEApp(mcp_sse_transport)
        transport_app = MCPTransportApp(streamable_app, mcp_sse_app)

        sse_transport = SseServerTransport(sse_message_path)
        sse_app = LegacySSEApp(sse_transport)

        return [
            Route(mcp_path, endpoint=transport_app),
            Mount(mcp_message_path, app=mcp_sse_transport.handle_post_message),
            Route(sse_path, endpoint=sse_app),
            Mount(sse_message_path, app=sse_transport.handle_post_message),
        ]

    async def health_check(request) -> PlainTextResponse:
        return PlainTextResponse("OK")

    routes: list[Route | Mount] = build_transport_routes(
        config.mcp_path,
        config.mcp_messages_path,
        config.sse_path,
        config.sse_messages_path,
    )

    if config.mcp_path != "/mcp":
        routes.extend(build_transport_routes("/mcp", "/mcp/messages/", "/sse", "/messages/"))
        routes.append(Route(f"{config.http_base_path}/health", endpoint=health_check))

    routes.append(Route("/health", endpoint=health_check))

    @asynccontextmanager
    async def lifespan(app: Starlette):
        async with session_manager.run():
            yield

    app = Starlette(routes=routes, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

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
