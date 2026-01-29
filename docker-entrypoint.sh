#!/usr/bin/env sh
set -eu

# Ensure mount points exist for common deployments (docker volume/bind mounts).
mkdir -p /app/data /app/logs

# Import tokens from GROK_COOKIES environment variable (if token.json doesn't exist or is empty)
if [ -n "${GROK_COOKIES:-}" ]; then
  TOKEN_FILE="/app/data/token.json"
  
  # Check if token.json exists and has tokens
  if [ ! -f "$TOKEN_FILE" ] || [ ! -s "$TOKEN_FILE" ] || ! grep -q '"ssoNormal"' "$TOKEN_FILE" 2>/dev/null; then
    echo "[Entrypoint] Importing tokens from GROK_COOKIES environment variable..."
    
    # Parse comma-separated tokens and build JSON
    python3 << 'PYTHON_SCRIPT'
import os
import json
import time
from pathlib import Path

token_file = Path("/app/data/token.json")
grok_cookies = os.getenv("GROK_COOKIES", "")

if not grok_cookies:
    print("[Entrypoint] GROK_COOKIES is empty, skipping import")
    exit(0)

# Parse tokens
tokens = [t.strip() for t in grok_cookies.split(",") if t.strip()]
if not tokens:
    print("[Entrypoint] No valid tokens found in GROK_COOKIES")
    exit(0)

# Build token data structure
token_data = {"ssoNormal": {}, "ssoSuper": {}}
timestamp = int(time.time() * 1000)

for token in tokens:
    token_data["ssoNormal"][token] = {
        "createdTime": timestamp,
        "remainingQueries": -1,
        "heavyremainingQueries": -1,
        "videoRemaining": -1,
        "videoLimit": -1,
        "status": "active",
        "failedCount": 0,
        "zeroCount": 0,
        "lastFailureTime": None,
        "lastFailureReason": None,
        "tags": [],
        "note": "Imported from GROK_COOKIES env var"
    }

# Write to file
token_file.parent.mkdir(parents=True, exist_ok=True)
with open(token_file, "w", encoding="utf-8") as f:
    json.dump(token_data, f, indent=2)

print(f"[Entrypoint] Successfully imported {len(tokens)} tokens to {token_file}")
PYTHON_SCRIPT
    
    if [ $? -eq 0 ]; then
      echo "[Entrypoint] Token import completed successfully"
    else
      echo "[Entrypoint] WARNING: Token import failed, service may not have available tokens"
    fi
  else
    echo "[Entrypoint] Token file exists and has data, skipping GROK_COOKIES import"
  fi
fi

# Start MCP proxy server (optional)
if [ "${MCP_ENABLED:-1}" = "1" ]; then
  python -m uvicorn mcp_proxy:app --host 0.0.0.0 --port 8001 &
fi

exec "$@"
