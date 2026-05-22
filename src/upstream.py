from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import httpx
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from src.config import Settings
from src.model_alias import ModelAliasResolver

logger = logging.getLogger(__name__)


def _resolve_auth(settings: Settings, authorization: str | None) -> str:
    if settings.use_client_auth and authorization:
        if authorization.lower().startswith("bearer "):
            return authorization.split(" ", 1)[1].strip()
        return authorization.strip()

    if settings.upstream_api_key:
        return settings.upstream_api_key

    raise HTTPException(
        status_code=500,
        detail="UPSTREAM_API_KEY is not set. Copy .env.example to .env and add your key.",
    )


def _upstream_chat_url(settings: Settings) -> str:
    if not settings.upstream_base_url:
        raise HTTPException(
            status_code=500,
            detail="upstream.base_url is empty in config.yaml",
        )
    return f"{settings.upstream_base_url}{settings.upstream_chat_path}"


async def forward_chat_completions(
    body: dict[str, Any],
    settings: Settings,
    resolver: ModelAliasResolver,
    authorization: str | None,
) -> Any:
    try:
        upstream_model = resolver.resolve(str(body.get("model", "")))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    payload = {**body, "model": upstream_model}
    token = _resolve_auth(settings, authorization)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    url = _upstream_chat_url(settings)

    logger.info("upstream request model=%s -> %s", body.get("model"), upstream_model)

    if payload.get("stream"):
        return await _stream_response(url, headers, payload, settings.upstream_timeout_seconds)

    return await _json_response(url, headers, payload, settings.upstream_timeout_seconds)


async def _json_response(
    url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(url, headers=headers, json=payload)
        except httpx.RequestError as exc:
            logger.exception("upstream connection failed")
            raise HTTPException(
                status_code=502, detail=f"Upstream connection failed: {exc}"
            ) from exc

    if resp.status_code >= 400:
        logger.warning("upstream error status=%s body=%s", resp.status_code, resp.text[:500])
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    try:
        return resp.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502, detail="Upstream returned non-JSON response"
        ) from exc


async def _stream_response(
    url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float
) -> StreamingResponse:
    client = httpx.AsyncClient(timeout=timeout)

    try:
        req = client.build_request("POST", url, headers=headers, json=payload)
        resp = await client.send(req, stream=True)
    except httpx.RequestError as exc:
        await client.aclose()
        logger.exception("upstream stream connection failed")
        raise HTTPException(
            status_code=502, detail=f"Upstream connection failed: {exc}"
        ) from exc

    if resp.status_code >= 400:
        text = await resp.aread()
        await resp.aclose()
        await client.aclose()
        detail = text.decode("utf-8", errors="replace")
        logger.warning("upstream stream error status=%s", resp.status_code)
        raise HTTPException(status_code=resp.status_code, detail=detail)

    async def generate() -> AsyncIterator[bytes]:
        try:
            async for chunk in resp.aiter_bytes():
                yield chunk
        finally:
            await resp.aclose()
            await client.aclose()

    return StreamingResponse(
        generate(),
        status_code=200,
        media_type="text/event-stream",
    )
