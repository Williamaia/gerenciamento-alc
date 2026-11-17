"""Recebimento dos eventos da Evolution API."""

import hashlib
import hmac
import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from frota_plus.config import Settings

logger = logging.getLogger("frota_plus.webhook")

WEBHOOK_PATH = "/webhooks/evolution"


def secret_matches(provided: str, expected: str) -> bool:
    if not expected:
        return False
    provided_hash = hashlib.sha256(provided.encode("utf-8")).digest()
    expected_hash = hashlib.sha256(expected.encode("utf-8")).digest()
    return hmac.compare_digest(provided_hash, expected_hash)


def presented_secrets(headers: Any) -> list[str]:
    found: list[str] = []
    authorization = headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        if token:
            found.append(token)
    api_key = headers.get("apikey", "").strip()
    if api_key:
        found.append(api_key)
    return found


def authorized(headers: Any, settings: Settings) -> bool:
    expected = settings.evolution_webhook_secret.strip()
    if not expected:
        return False
    matched = False
    for candidate in presented_secrets(headers):
        matched = secret_matches(candidate, expected) or matched
    return matched


def message_id(payload: dict[str, Any]) -> str | None:
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    key = data.get("key")
    if isinstance(key, dict) and key.get("id"):
        return str(key["id"])
    if data.get("id"):
        return str(data["id"])
    return None


def register_evolution_webhook(app: FastAPI) -> None:
    @app.post(WEBHOOK_PATH)
    async def receive_evolution_webhook(request: Request) -> JSONResponse:
        settings: Settings = request.app.state.settings
        if not settings.webhook_configured:
            return JSONResponse(status_code=503, content={"error": "webhook_not_configured"})
        if not authorized(request.headers, settings):
            return JSONResponse(status_code=401, content={"error": "unauthorized"})

        try:
            payload = await request.json()
        except Exception:
            return JSONResponse(status_code=400, content={"error": "invalid_json"})
        if not isinstance(payload, dict):
            return JSONResponse(status_code=400, content={"error": "invalid_json"})

        payload.pop("apikey", None)
        event_name = str(payload.get("event") or "")
        identifier = message_id(payload)
        seen: set[str] = request.app.state.seen_message_ids
        duplicate = bool(identifier and identifier in seen)
        if identifier and not duplicate:
            seen.add(identifier)

        logger.info(
            "evolution_event event=%s message_id=%s duplicate=%s",
            event_name,
            identifier or "",
            duplicate,
        )
        if not duplicate:
            try:
                request.app.state.service.handle(payload)
            except Exception:
                logger.exception("falha_ao_processar_evento")
        return JSONResponse(
            status_code=200,
            content={"accepted": True, "duplicate": duplicate},
        )
