from fastapi.testclient import TestClient

from frota_plus.config import Settings
from frota_plus.main import create_app

SECRET = "segredo-de-teste"
AGENT_KEY = "sk-proj-teste-nao-usar"


def build_client(**overrides: object) -> TestClient:
    values = {
        "evolution_webhook_secret": SECRET,
        "ai_api_key": AGENT_KEY,
        "public_base_url": "",
        "port": 8000,
    }
    values.update(overrides)
    return TestClient(create_app(Settings(**values)))


def test_health_mostra_url_sem_segredo() -> None:
    client = build_client(public_base_url="https://frota.exemplo")
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["webhookPath"] == "/webhooks/evolution"
    assert body["webhookUrl"] == "https://frota.exemplo/webhooks/evolution"
    assert body["webhookConfigured"] is True
    assert AGENT_KEY not in response.text
    assert SECRET not in response.text


def test_health_local_quando_nao_ha_base_publica() -> None:
    response = build_client().get("/health")
    assert response.json()["webhookUrl"] == "http://127.0.0.1:8000/webhooks/evolution"


def test_webhook_sem_segredo_configurado_nao_processa() -> None:
    client = build_client(evolution_webhook_secret="")
    response = client.post("/webhooks/evolution", json={"event": "messages.upsert"})
    assert response.status_code == 503
    assert response.json()["error"] == "webhook_not_configured"


def test_webhook_com_segredo_errado_nao_processa() -> None:
    response = build_client().post(
        "/webhooks/evolution",
        json={"event": "messages.upsert", "apikey": "nao-devolver"},
        headers={"Authorization": "Bearer errado"},
    )
    assert response.status_code == 401
    assert "nao-devolver" not in response.text
    assert "pagamento" not in response.text


def test_webhook_aceita_bearer_e_deduplica() -> None:
    client = build_client()
    payload = {
        "event": "messages.upsert",
        "apikey": "chave-da-evolution",
        "data": {"key": {"id": "MSG1"}},
    }
    headers = {"Authorization": f"Bearer {SECRET}"}
    first = client.post("/webhooks/evolution", json=payload, headers=headers)
    second = client.post("/webhooks/evolution", json=payload, headers=headers)
    assert first.status_code == 200
    assert first.json() == {"accepted": True, "duplicate": False}
    assert second.json() == {"accepted": True, "duplicate": True}
    assert "chave-da-evolution" not in first.text
    assert AGENT_KEY not in first.text


def test_webhook_aceita_cabecalho_apikey() -> None:
    response = build_client().post(
        "/webhooks/evolution",
        json={"event": "messages.upsert", "data": {"key": {"id": "MSG2"}}},
        headers={"apikey": SECRET},
    )
    assert response.status_code == 200
    assert response.json()["accepted"] is True


def test_json_invalido_nao_cria_efeito() -> None:
    response = build_client().post(
        "/webhooks/evolution",
        content="{",
        headers={"Authorization": f"Bearer {SECRET}", "Content-Type": "application/json"},
    )
    assert response.status_code == 400
