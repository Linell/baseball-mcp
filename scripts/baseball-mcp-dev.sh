#!/usr/bin/env bash
# Simple wrapper to run the local Baseball MCP server under development.
#
# Usage:
#   ./scripts/baseball-mcp-dev.sh            # runs STDIO transport (default)
#   ./scripts/baseball-mcp-dev.sh http -p 9000 # passes args through to CLI
#
# This avoids PATH / shebang issues when launching from GUI apps like Claude Desktop.
set -euo pipefail

# Resolve repository root (directory containing this script, then up one level)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Ensure Homebrew bin comes first (helps when GUI apps have limited PATH)
export PATH="/opt/homebrew/bin:$PATH"

# Make src/ importable when package isn't installed for this interpreter
# Use parameter expansion to handle an unset PYTHONPATH when `set -u` is enabled
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

# Prefer project virtualenv if it exists (keeps dependencies isolated)
if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  exec "$ROOT_DIR/.venv/bin/python" -m baseball_mcp.cli "$@"
fi

# Fallback to system python3
exec python3 -m baseball_mcp.cli "$@" 