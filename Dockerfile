# Use Python 3.11 as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip resolver – makes dependency installation faster and deterministic
RUN pip install --no-cache-dir --upgrade pip

# Copy requirements and README (needed for package metadata)
COPY pyproject.toml ./
COPY README.md ./
COPY LICENSE ./

# Copy source code (needed for package installation)
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create cache directory
RUN mkdir -p ~/.config/baseball-mcp

# Health check with longer timeouts for slow-starting dependencies
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=5 \
    CMD curl -f http://localhost:${PORT:-3000}/health || exit 1

# Document the port Smithery will map
EXPOSE 3000

# Run the HTTP server
CMD ["python", "-m", "baseball_mcp.http"] 