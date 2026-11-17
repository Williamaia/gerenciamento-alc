"""Configuração lida do ambiente. Segredos não têm valor padrão."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "0.0.0.0"
    port: int = 8000
    public_base_url: str = ""
    evolution_webhook_secret: str = ""
    ai_provider: str = ""
    ai_model: str = ""
    ai_api_key: str = ""
    default_timezone: str = "America/Sao_Paulo"

    @property
    def webhook_path(self) -> str:
        return "/webhooks/evolution"

    @property
    def webhook_url(self) -> str:
        base = self.public_base_url.strip().rstrip("/")
        if base:
            return f"{base}{self.webhook_path}"
        return f"http://127.0.0.1:{self.port}{self.webhook_path}"

    @property
    def webhook_configured(self) -> bool:
        return bool(self.evolution_webhook_secret.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
