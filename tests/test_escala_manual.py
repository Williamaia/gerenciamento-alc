from datetime import date, datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from frota_plus.config import Settings
from frota_plus.domain.dates import SAO_PAULO
from frota_plus.main import create_app
from frota_plus.outbound import RecordingOutbound
from frota_plus.store import Store

SECRET = "segredo-de-teste"
ORIGIN = "origem@g.us"
CONTROL = "controle@g.us"
DRIVER = "556599607901"
TODAY = datetime(2026, 11, 20, 8, 10, tzinfo=SAO_PAULO)
DAWN = datetime(2026, 11, 20, 0, 40, tzinfo=SAO_PAULO)


class InterpreterQueNaoPodeRodar:
    def read(self, caption: str, image_jpeg: bytes | None, driver_name: str) -> dict:
        raise AssertionError("a escala manual nao le imagem")


def client_for(store: Store, outbound: RecordingOutbound, secret: str = SECRET) -> TestClient:
    settings = Settings(
        evolution_webhook_secret=secret,
        whatsapp_origin_group_id=ORIGIN,
        whatsapp_control_group_id=CONTROL,
        whatsapp_driver_number=DRIVER,
        fuel_daily_amount="90",
        data_path="",
        evolution_api_base_url="",
        evolution_api_key="",
        evolution_instance="",
        ai_api_key="",
    )
    app = create_app(
        settings,
        outbound=outbound,
        interpreter=InterpreterQueNaoPodeRodar(),
        store=store,
    )
    return TestClient(app)


def escala(codigo: str = "D9_PM1", cidades: list[str] | None = None) -> dict:
    body: dict = {
        "data": "20/11/2026",
        "rotas": [{"codigo": codigo, "cidades": cidades or ["Congonhinhas"]}],
    }
    return body


def post_escala(client: TestClient, body: dict | None = None, secret: str | None = SECRET, header: str = "bearer"):
    headers = {}
    if secret is not None and header == "bearer":
        headers["Authorization"] = f"Bearer {secret}"
    if secret is not None and header == "apikey":
        headers["apikey"] = secret
    return client.post("/operacoes/escala", json=body if body is not None else escala(), headers=headers)


def test_credencial_ausente_ou_errada_nao_grava_nem_envia(caplog) -> None:
    store = Store(None)
    outbound = RecordingOutbound()
    client = client_for(store, outbound)
    missing = post_escala(client, secret=None)
    wrong = post_escala(client, secret="token-que-nao-pode-aparecer")
    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert store.days == {}
    assert outbound.sent == []
    assert "token-que-nao-pode-aparecer" not in missing.text
    assert "token-que-nao-pode-aparecer" not in wrong.text
    assert "token-que-nao-pode-aparecer" not in caplog.text


def test_segredo_vazio_nao_grava() -> None:
    store = Store(None)
    outbound = RecordingOutbound()
    client = client_for(store, outbound, secret="")
    response = post_escala(client)
    assert response.status_code == 503
    assert store.days == {}
    assert outbound.sent == []


def test_corpo_incompleto_nao_altera_o_dia() -> None:
    store = Store(None)
    outbound = RecordingOutbound()
    client = client_for(store, outbound)
    client.app.state.clock = lambda: TODAY
    without_city = {"data": "20/11/2026", "rotas": [{"codigo": "D9_PM1", "cidades": []}]}
    without_code = {"data": "20/11/2026", "rotas": [{"cidades": ["Congonhinhas"]}]}
    without_date = {"rotas": [{"codigo": "D9_PM1", "cidades": ["Congonhinhas"]}]}
    assert post_escala(client, without_city).status_code == 400
    assert post_escala(client, without_code).status_code == 400
    assert post_escala(client, without_date).status_code == 400
    assert store.days == {}
    assert outbound.sent == []


def test_grava_rotas_sem_parada_nem_quilometragem() -> None:
    store = Store(None)
    outbound = RecordingOutbound()
    client = client_for(store, outbound)
    client.app.state.clock = lambda: TODAY
    body = escala(cidades=["Abatiá", "Congonhinhas"])
    response = post_escala(client, body, header="apikey")
    assert response.status_code == 200
    record = store.day(date(2026, 11, 20))
    assert record is not None
    assert record["routes"] == [
        {"code": "D9_PM1", "cities": ["Abatiá", "Congonhinhas"], "shared": False}
    ]
    assert record["stops"] is None
    assert record.get("km_ida") is None
    assert record.get("km_volta") is None


def test_depois_das_oito_pede_paradas_so_ao_motorista() -> None:
    store = Store(None)
    outbound = RecordingOutbound()
    client = client_for(store, outbound)
    client.app.state.clock = lambda: TODAY
    response = post_escala(client)
    assert response.status_code == 200
    assert response.json()["pedidoEnviado"] is True
    assert [item[0] for item in outbound.sent] == [DRIVER]
    assert "D9_PM1" in outbound.sent[0][1]
    assert "Por favor, informe a quantidade de paradas" in outbound.sent[0][1]
    assert ORIGIN not in [item[0] for item in outbound.sent]
    assert CONTROL not in [item[0] for item in outbound.sent]


def test_madrugada_deixa_o_pedido_para_as_oito() -> None:
    store = Store(None)
    outbound = RecordingOutbound()
    client = client_for(store, outbound)
    client.app.state.clock = lambda: DAWN
    response = post_escala(client)
    assert response.status_code == 200
    assert response.json()["pedidoEnviado"] is False
    assert outbound.sent == []
    record = store.day(date(2026, 11, 20))
    assert record is not None
    assert record["stops_asked"] is False
    client.app.state.service.tick(datetime(2026, 11, 20, 8, 0, tzinfo=SAO_PAULO))
    assert [item[0] for item in outbound.sent] == [DRIVER]
    assert ORIGIN not in [item[0] for item in outbound.sent]


def test_mesmos_codigos_nao_repetem_o_pedido() -> None:
    store = Store(None)
    outbound = RecordingOutbound()
    client = client_for(store, outbound)
    client.app.state.clock = lambda: TODAY
    assert post_escala(client).status_code == 200
    again = post_escala(client)
    assert again.status_code == 200
    assert again.json()["pedidoEnviado"] is False
    assert len(outbound.sent) == 1


def test_codigos_novos_substituem_e_pedem_de_novo() -> None:
    store = Store(None)
    outbound = RecordingOutbound()
    client = client_for(store, outbound)
    client.app.state.clock = lambda: TODAY
    post_escala(client)
    corrected = post_escala(client, escala("C5_PM1", ["Nova Fátima", "Congonhinhas"]))
    assert corrected.status_code == 200
    assert corrected.json()["pedidoEnviado"] is True
    record = store.day(date(2026, 11, 20))
    assert record is not None
    assert record["stops"] is None
    assert record["routes"][0]["code"] == "C5_PM1"
    assert record["routes"][0]["cities"] == ["Nova Fátima", "Congonhinhas"]
    assert len(outbound.sent) == 2
    assert "C5_PM1" in outbound.sent[1][1]
    assert [item[0] for item in outbound.sent] == [DRIVER, DRIVER]


def test_dia_com_paradas_nao_e_substituido() -> None:
    store = Store(None)
    outbound = RecordingOutbound()
    client = client_for(store, outbound)
    client.app.state.clock = lambda: datetime(2026, 11, 19, 8, 10, tzinfo=SAO_PAULO)
    operation = date(2026, 11, 19)
    record = store.ensure_day(operation, Decimal("90"))
    record["routes"] = [{"code": "C5_PM1", "cities": ["Nova Fátima"], "shared": False}]
    record["stops"] = 63
    record["km_ida"] = "74"
    record["km_volta"] = "73"
    store.put_day(operation, record)
    response = post_escala(client, {"data": "19/11/2026", "rotas": [{"codigo": "D9_PM1", "cidades": ["Congonhinhas"]}]})
    assert response.status_code == 409
    kept = store.day(operation)
    assert kept is not None
    assert kept["stops"] == 63
    assert kept["routes"][0]["code"] == "C5_PM1"
    assert kept["km_ida"] == "74"
    assert outbound.sent == []
