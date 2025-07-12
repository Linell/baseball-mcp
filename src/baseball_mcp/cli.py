"""Command-line interface for baseball-mcp."""

from __future__ import annotations

import asyncio

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
def http(port: int = typer.Option(8000, "--port", "-p")) -> None:
    """Run the HTTP MCP server (ASGI)."""

    import uvicorn  # noqa: S404  (runtime import)

    uvicorn.run("baseball_mcp.http:app", host="0.0.0.0", port=port, workers=1)


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


def main() -> None:  # entry-point for console_scripts
    cli()


if __name__ == "__main__":
    cli()
