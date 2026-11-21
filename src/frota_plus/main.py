"""Serviço HTTP do Frota Plus."""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

logger = logging.getLogger("frota_plus")

from frota_plus.config import Settings, get_settings
from frota_plus.confirmed import apply_confirmed_days
from frota_plus.interpreter import OpenAIInterpreter
from frota_plus.outbound import EvolutionOutbound, Outbound
from frota_plus.schedule import run_schedule
from frota_plus.service import DailyService
from frota_plus.store import Store
from frota_plus.webhooks.escala import register_manual_scale
from frota_plus.webhooks.evolution import WEBHOOK_PATH, register_evolution_webhook


def create_app(
    settings: Settings | None = None,
    *,
    outbound: Outbound | None = None,
    interpreter=None,
    store: Store | None = None,
    remember_confirmed: bool = False,
) -> FastAPI:
    current = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if remember_confirmed:
            try:
                app.state.service.refresh_pending_routes()
            except Exception:
                logger.exception("recalculo_da_rota")
        task = asyncio.create_task(run_schedule(app))
        yield
        task.cancel()

    app = FastAPI(title="Frota Plus", version="0.1.0", lifespan=lifespan)
    app.state.settings = current
    app.state.seen_message_ids = set()
    app.state.store = store or Store(Path(current.data_path) if current.data_path else None)
    app.state.outbound = outbound or EvolutionOutbound(
        current.evolution_api_base_url,
        current.evolution_api_key,
        current.evolution_instance,
    )
    app.state.interpreter = interpreter or OpenAIInterpreter(current.ai_api_key, current.ai_model)
    if remember_confirmed:
        apply_confirmed_days(app.state.store, current.fuel_default)
    app.state.service = DailyService(
        current,
        app.state.store,
        app.state.outbound,
        app.state.interpreter,
    )
    hook = getattr(app.state.outbound, "on_http_error", None)
    if hook is None and hasattr(app.state.outbound, "on_http_error"):
        app.state.outbound.on_http_error = app.state.service.report_send_failure

    @app.get("/health")
    def health() -> dict[str, str | bool]:
        return {
            "service": "frota-plus",
            "webhookPath": current.webhook_path,
            "webhookUrl": current.webhook_url,
            "webhookConfigured": current.webhook_configured,
        }

    register_evolution_webhook(app)
    register_manual_scale(app)
    if WEBHOOK_PATH != current.webhook_path:
        raise RuntimeError("O caminho do webhook divergiu da configuração.")
    return app


app = create_app(remember_confirmed=True)
