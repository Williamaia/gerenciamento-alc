"""Registro manual de uma escala que não chegou pelo WhatsApp."""

import logging
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from frota_plus.config import Settings
from frota_plus.domain.dates import SAO_PAULO
from frota_plus.webhooks.evolution import authorized

logger = logging.getLogger("frota_plus.escala")

MANUAL_SCALE_PATH = "/operacoes/escala"


def register_manual_scale(app: FastAPI) -> None:
    @app.post(MANUAL_SCALE_PATH)
    async def receive_manual_scale(request: Request) -> JSONResponse:
        settings: Settings = request.app.state.settings
        if not settings.webhook_configured:
            return JSONResponse(status_code=503, content={"error": "webhook_not_configured"})
        if not authorized(request.headers, settings):
            return JSONResponse(status_code=401, content={"error": "unauthorized"})
        try:
            payload: Any = await request.json()
        except Exception:
            return JSONResponse(status_code=400, content={"error": "invalid_body"})
        if not isinstance(payload, dict):
            return JSONResponse(status_code=400, content={"error": "invalid_body"})
        clock = getattr(request.app.state, "clock", None)
        now = clock() if clock is not None else datetime.now(SAO_PAULO)
        status, body = request.app.state.service.register_manual_scale(payload, now)
        return JSONResponse(status_code=status, content=body)
