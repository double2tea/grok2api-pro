#!/usr/bin/env sh
set -eu

# Ensure mount points exist for common deployments (docker volume/bind mounts).
mkdir -p /app/data /app/logs

# Start MCP proxy server (optional)
if [ "${MCP_ENABLED:-1}" = "1" ]; then
  python -m uvicorn mcp_proxy:app --host 0.0.0.0 --port 8001 &
fi

exec "$@"
