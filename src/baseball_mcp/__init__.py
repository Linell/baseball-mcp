"""Baseball MCP Server - A Model Context Protocol server for baseball data."""

__version__ = "0.1.0"
__author__ = "Linell Bonnette"
__email__ = "tlbonnette@gmail.com"

# Public re-exports
from .server import BaseballMCPServer

__all__ = [
    "BaseballMCPServer",
]
