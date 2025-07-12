"""Main entry point for the baseball-mcp HTTP server."""

import os

from baseball_mcp.http import HTTPServer


def main() -> None:
    """Run the HTTP server."""
    server = HTTPServer()

    # Use PORT environment variable
    port = int(os.environ.get("PORT", 3000))
    host = os.environ.get("HOST", "0.0.0.0")

    server.run(host=host, port=port)

if __name__ == "__main__":
    main()
