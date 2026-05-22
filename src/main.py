from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request

from src.config import Settings, load_settings
from src.model_alias import ModelAliasResolver
from src.upstream import forward_chat_completions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings: Settings
resolver: ModelAliasResolver


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global settings, resolver
    settings = load_settings()
    resolver = ModelAliasResolver(settings.model_aliases)
    logger.info(
        "Cursor proxy ready [%s] on %s:%s (%d model aliases)",
        settings.provider,
        settings.host,
        settings.port,
        len(settings.model_aliases),
    )
    if not settings.upstream_api_key and not settings.use_client_auth:
        logger.warning("UPSTREAM_API_KEY is empty. Set .env before using Cursor.")
    yield


app = FastAPI(title="Cursor OpenAI Bridge", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "provider": settings.provider,
        "models": resolver.cursor_names,
        "upstream": settings.upstream_base_url,
        "chat_path": settings.upstream_chat_path,
    }


@app.get("/v1/models")
async def list_models() -> dict[str, Any]:
    created = 1700000000
    data = [
        {
            "id": name,
            "object": "model",
            "created": created,
            "owned_by": settings.provider,
        }
        for name in resolver.cursor_names
    ]
    return {"object": "list", "data": data}


async def _handle_chat(
    request: Request, authorization: str | None = Header(default=None)
) -> Any:
    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")

    return await forward_chat_completions(body, settings, resolver, authorization)


@app.post("/v1/chat/completions")
async def chat_completions_v1(
    request: Request, authorization: str | None = Header(default=None)
):
    return await _handle_chat(request, authorization)


@app.post("/chat/completions")
async def chat_completions_compat(
    request: Request, authorization: str | None = Header(default=None)
):
    return await _handle_chat(request, authorization)


def run() -> None:
    import uvicorn

    s = load_settings()
    uvicorn.run(
        "src.main:app",
        host=s.host,
        port=s.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
