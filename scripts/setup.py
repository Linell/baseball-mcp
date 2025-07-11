#!/usr/bin/env python3
"""Setup script for baseball-mcp development environment."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def main():
    """Main setup function."""
    print("🏗️  Setting up baseball-mcp development environment...")
    print()
    
    project_root = Path(__file__).parent.parent
    
    # Change to project root
    import os
    os.chdir(project_root)
    
    # Check if we're in a virtual environment
    if sys.prefix == sys.base_prefix:
        print("⚠️  Warning: You're not in a virtual environment!")
        print("   Consider running: python -m venv venv && source venv/bin/activate")
        print()
    
    # Install package in development mode
    success = run_command(
        "pip install -e .[dev]",
        "Installing package in development mode"
    )
    
    if not success:
        print("❌ Failed to install package. Exiting.")
        sys.exit(1)
    
    # Install pre-commit hooks
    success = run_command(
        "pre-commit install",
        "Installing pre-commit hooks"
    )
    
    if not success:
        print("⚠️  Pre-commit hooks installation failed. You can install them later with: pre-commit install")
    
    # Run initial tests
    success = run_command(
        "pytest",
        "Running initial tests"
    )
    
    if not success:
        print("⚠️  Initial tests failed. Please check the test setup.")
    
    print()
    print("🎉 Setup complete!")
    print()
    print("Next steps:")
    print("1. Fill out the README.md with your project details")
    print("2. Update the author information in pyproject.toml")
    print("3. Implement the baseball data functionality in src/baseball_mcp/server.py")
    print("4. Add more tests as you develop features")
    print()
    print("Development commands:")
    print("- make help          # Show available commands")
    print("- make run           # Run the MCP server")
    print("- make test          # Run tests")
    print("- make lint          # Run linting")
    print("- make format        # Format code")
    print("- make check         # Run all checks")


if __name__ == "__main__":
    main() 