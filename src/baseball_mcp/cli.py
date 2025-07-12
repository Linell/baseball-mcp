"""Command-line interface for baseball-mcp."""

from __future__ import annotations

import asyncio
import os

import typer

from baseball_mcp.cache import Cache
from baseball_mcp.server import BaseballMCPServer

cli = typer.Typer(help="Baseball-MCP utilities", invoke_without_command=True)


@cli.callback(invoke_without_command=True)
def _default(ctx: typer.Context) -> None:  # noqa: D401
    """Run as STDIO when called without subcommands."""

    if ctx.invoked_subcommand is None:
        asyncio.run(BaseballMCPServer().run())


@cli.command()
def http(
    port: int = typer.Option(3000, "--port", "-p", help="Port to listen on"),
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
) -> None:
    """Run the HTTP MCP server."""

    # Import here to avoid circular imports
    from baseball_mcp.http import HTTPServer

    # Set PORT environment variable if provided
    if port != 3000:
        os.environ["PORT"] = str(port)

    server = HTTPServer()
    server.run(host=host, port=port)


@cli.command(name="cache-reset")
def cache_reset(confirm: bool = typer.Option(False, "--confirm", prompt="Confirm cache reset?")) -> None:  # noqa: D401,E501
    """Wipe the local cache."""

    if confirm:
        Cache().reset()
        typer.echo("Cache cleared.")
    else:
        typer.echo("Cancelled – pass --confirm to proceed.")


@cli.command()
def run() -> None:
    """Explicit STDIO server command."""

    asyncio.run(BaseballMCPServer().run())


@cli.command()
def health() -> None:
    """Check server health."""

    import requests

    port = int(os.environ.get("PORT", 3000))

    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        if response.status_code == 200:
            typer.echo("✅ Server is healthy")
        else:
            typer.echo(f"❌ Server returned status {response.status_code}")
            raise typer.Exit(1)
    except requests.RequestException as e:
        typer.echo(f"❌ Server health check failed: {e}")
        raise typer.Exit(1) from e


def main() -> None:  # entry-point for console_scripts
    cli()


if __name__ == "__main__":
    cli()
