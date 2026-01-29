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

# Initialize setting.toml from environment variables
if [ ! -f "/app/data/setting.toml" ]; then
  echo "[Entrypoint] Initializing setting.toml from environment variables..."
  python3 << 'PYTHON_SCRIPT'
import os
import toml
from pathlib import Path

# Paths
example_path = Path("data/setting.example.toml")
config_path = Path("/app/data/setting.toml")
config_path.parent.mkdir(parents=True, exist_ok=True)

# Load default/example config
if example_path.exists():
    with open(example_path, "r", encoding="utf-8") as f:
        config = toml.load(f)
else:
    # Fallback default structure
    config = {
        "grok": {
            "api_key": "",
            "x_statsig_id": "",
            "retry_status_codes": [401, 429]
        },
        "global": {
            "base_url": "http://localhost:8001",
            "admin_password": "admin"
        }
    }

# Inject environment variables
# [grok] section
if api_key := os.getenv("API_KEY"):
    config.setdefault("grok", {})["api_key"] = api_key
    
if x_statsig_id := os.getenv("X_STATSIG_ID"):
    config.setdefault("grok", {})["x_statsig_id"] = x_statsig_id

# [global] section
if admin_password := os.getenv("ADMIN_PASSWORD") or os.getenv("PASSWORD"):
    config.setdefault("global", {})["admin_password"] = admin_password

if base_url := os.getenv("BASE_URL"):
    config.setdefault("global", {})["base_url"] = base_url

# Save config
with open(config_path, "w", encoding="utf-8") as f:
    toml.dump(config, f)

print(f"[Entrypoint] Config generated at {config_path}")
PYTHON_SCRIPT
fi

# Start MCP proxy server (optional)
if [ "${MCP_ENABLED:-1}" = "1" ]; then
  python -m uvicorn mcp_proxy:app --host 0.0.0.0 --port 8001 &
fi

exec "$@"
