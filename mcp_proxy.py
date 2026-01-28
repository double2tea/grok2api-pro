import os

import httpx
from fastapi import FastAPI, HTTPException, Request


MCP_API_KEY = os.getenv("MCP_API_KEY", "")
GROK_BASE_URL = os.getenv("GROK_BASE_URL", "http://localhost:8000")

app = FastAPI(title="Grok2API MCP Proxy")


def _verify_bearer(request: Request) -> None:
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid Authorization header"
        )
    token = auth_header.replace("Bearer ", "", 1)
    if not MCP_API_KEY or token != MCP_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


async def _proxy(request: Request, path: str):
    _verify_bearer(request)
    target_url = f"{GROK_BASE_URL}{path}"
    async with httpx.AsyncClient(timeout=120) as client:
        if request.method == "GET":
            response = await client.get(target_url, params=request.query_params)
        else:
            body = await request.body()
            response = await client.request(
                request.method,
                target_url,
                content=body,
                headers={
                    "Content-Type": request.headers.get(
                        "content-type", "application/json"
                    )
                },
            )
    return response.status_code, response.headers, response.content


@app.get("/v1/models")
async def list_models(request: Request):
    status, headers, content = await _proxy(request, "/v1/models")
    return app.response_class(
        content, status_code=status, media_type=headers.get("content-type")
    )


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    status, headers, content = await _proxy(request, "/v1/chat/completions")
    return app.response_class(
        content, status_code=status, media_type=headers.get("content-type")
    )


@app.post("/v1/images/generations")
async def images_generations(request: Request):
    status, headers, content = await _proxy(request, "/v1/images/generations")
    return app.response_class(
        content, status_code=status, media_type=headers.get("content-type")
    )


@app.post("/v1/video/generations")
async def video_generations(request: Request):
    status, headers, content = await _proxy(request, "/v1/video/generations")
    return app.response_class(
        content, status_code=status, media_type=headers.get("content-type")
    )
