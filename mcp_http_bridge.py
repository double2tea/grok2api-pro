#!/usr/bin/env python3
"""
MCP HTTP Bridge - Converts HTTP MCP server to stdio transport for Claude Code

Usage:
    python3 mcp_http_bridge.py

Environment variables:
    MCP_SERVER_URL: Remote MCP server URL (default: http://localhost:8001)
    MCP_API_KEY: API key for authentication
"""

import asyncio
import json
import os
import sys
from typing import Any

import httpx


# Configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
MCP_API_KEY = os.getenv("MCP_API_KEY", "")


async def call_mcp_method(method: str, params: dict | None = None) -> dict[str, Any]:
    """Call a method on the remote MCP server."""
    msg_id = params.get("id", 1) if params else 1

    # Handle initialize
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {},
                },
                "serverInfo": {
                    "name": "grok2api-mcp-bridge",
                    "version": "1.0.0",
                },
            },
        }

    # Handle notifications/initialized (no-op)
    if method == "notifications/initialized":
        return {"jsonrpc": "2.0", "id": msg_id, "result": None}

    # Handle tools/list
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": [
                    {
                        "name": "chat_completions",
                        "description": "Chat completions using Grok models",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "model": {"type": "string", "description": "Model ID"},
                                "messages": {
                                    "type": "array",
                                    "description": "Chat messages",
                                },
                                "stream": {
                                    "type": "boolean",
                                    "description": "Enable streaming",
                                },
                            },
                            "required": ["model", "messages"],
                        },
                    },
                    {
                        "name": "list_models",
                        "description": "List available Grok models",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                        },
                    },
                ]
            },
        }

    # Handle tools/call
    if method == "tools/call":
        tool_name = params.get("name") if params else None
        arguments = params.get("arguments", {}) if params else {}

        if tool_name == "chat_completions":
            url = f"{MCP_SERVER_URL}/v1/chat/completions"
            http_method = "POST"
            json_data = arguments
        elif tool_name == "list_models":
            url = f"{MCP_SERVER_URL}/v1/models"
            http_method = "GET"
            json_data = None
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
            }

        # Make HTTP request
        headers = {"Content-Type": "application/json"}
        if MCP_API_KEY:
            headers["Authorization"] = f"Bearer {MCP_API_KEY}"

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                if http_method == "GET":
                    response = await client.get(url, headers=headers)
                else:
                    response = await client.post(url, headers=headers, json=json_data)

                if response.status_code == 200:
                    result = response.json()
                else:
                    result = {
                        "error": {
                            "code": response.status_code,
                            "message": response.text,
                        }
                    }

                return {"jsonrpc": "2.0", "id": msg_id, "result": result}
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32603, "message": str(e)},
            }

    # Unknown method
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"},
    }


async def handle_stdio() -> None:
    """Handle JSON-RPC messages from stdin and write responses to stdout."""
    # Set up async stdin reader
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader(loop=loop)
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    # Process messages line by line
    while True:
        try:
            line = await reader.readline()
            if not line:
                break

            # Parse JSON-RPC message
            msg = json.loads(line.decode())
            method = msg.get("method")
            msg_id = msg.get("id")
            params = msg.get("params", {})

            # Add id to params for tracking
            if msg_id is not None:
                params["id"] = msg_id

            # Handle request
            if method:
                response = await call_mcp_method(method, params)

                # Write response to stdout
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

        except json.JSONDecodeError as e:
            # Return parse error
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"},
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()

        except Exception as e:
            # Return internal error
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    # Log startup to stderr (stdout is reserved for JSON-RPC)
    print(f"MCP Bridge connecting to {MCP_SERVER_URL}", file=sys.stderr)
    print(f"API Key configured: {bool(MCP_API_KEY)}", file=sys.stderr)

    # Run stdio handler
    asyncio.run(handle_stdio())
