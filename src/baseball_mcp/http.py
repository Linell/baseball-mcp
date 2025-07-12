"""ASGI entry-point exposing the Baseball MCP server over HTTP."""

from mcp.server.streamable_http import streamable_http_server  # type: ignore

from baseball_mcp.server import BaseballMCPServer

_server = BaseballMCPServer()
app = streamable_http_server(_server.server)
