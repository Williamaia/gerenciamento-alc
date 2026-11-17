"""Serviço HTTP do Frota Plus."""

from fastapi import FastAPI

from frota_plus.config import Settings, get_settings
from frota_plus.webhooks.evolution import WEBHOOK_PATH, register_evolution_webhook


def create_app(settings: Settings | None = None) -> FastAPI:
    current = settings or get_settings()
    app = FastAPI(title="Frota Plus", version="0.1.0")
    app.state.settings = current
    app.state.seen_message_ids = set()

    @app.get("/health")
    def health() -> dict[str, str | bool]:
        return {
            "service": "frota-plus",
            "webhookPath": current.webhook_path,
            "webhookUrl": current.webhook_url,
            "webhookConfigured": current.webhook_configured,
        }

    register_evolution_webhook(app)
    if WEBHOOK_PATH != current.webhook_path:
        raise RuntimeError("O caminho do webhook divergiu da configuração.")
    return app


app = create_app()
