from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from frota_plus.commands import FuelCommand, MaintenanceCommand, PnrCommand, parse_command
from frota_plus.config import Settings
from frota_plus.domain.dates import SAO_PAULO, read_operation_date
from frota_plus.domain.distance import normalize_city
from frota_plus.domain.money import day_profit, driver_pay, freight_for_km, stop_bonus
from frota_plus.routing import DistanceBook
from frota_plus.main import create_app
from frota_plus.outbound import RecordingOutbound
from frota_plus.store import Store

SECRET = "segredo-de-teste"
ORIGIN = "origem@g.us"
CONTROL = "controle@g.us"
DRIVER = "556599607901"


class FixedInterpreter:
    def read(self, caption: str, image_jpeg: bytes | None, driver_name: str) -> dict:
        return {
            "confident": True,
            "routes": [{"code": "D9_PM1", "cities": ["Congonhinhas"], "shared": False}],
        }


def client_for(store: Store, outbound: RecordingOutbound) -> TestClient:
    settings = Settings(
        evolution_webhook_secret=SECRET,
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
    return TestClient(create_app(settings, outbound=outbound, interpreter=FixedInterpreter(), store=store))


def test_faixas_de_parada_e_frete() -> None:
    assert stop_bonus(1) == Decimal("0.35")
    assert stop_bonus(60) == Decimal("21.00")
    assert stop_bonus(61) == Decimal("22.90")
    assert stop_bonus(90) == Decimal("78.00")
    assert stop_bonus(91) == Decimal("78.90")
    assert stop_bonus(95) == Decimal("82.50")
    assert stop_bonus(35) == Decimal("12.25")
    assert freight_for_km(Decimal("100")) == Decimal("235.00")
    assert freight_for_km(Decimal("146")) == Decimal("260.00")
    assert freight_for_km(Decimal("301")) == Decimal("380.00")
    assert driver_pay(1, 0) == Decimal("100.00")
    assert driver_pay(1, 1) == Decimal("150.00")
    assert day_profit(Decimal("277.25"), Decimal("100"), Decimal("90"), Decimal("0")) == Decimal("87.25")


def test_soma_km_de_cada_cidade() -> None:
    def fetch(city: str):
        table = {
            "jacarezinho": (Decimal("26"), Decimal("27")),
            "andira": (Decimal("38"), Decimal("40")),
        }
        return table.get(normalize_city(city))

    book = DistanceBook(Store(None), fetch)
    distance = book.for_routes(
        [
            {"cities": ["Congonhinhas", "Jacarezinho"]},
            {"cities": ["Andirá"]},
        ]
    )
    assert distance == (Decimal("137"), Decimal("140"))
    missing = book.for_routes([{"cities": ["Cidade Que Nao Existe"]}])
    assert missing is None


def test_data_nao_depende_da_frase() -> None:
    received = date(2026, 11, 17)
    follow = read_operation_date("Segue a escala 17/11", received)
    other = read_operation_date("escala de amanhã 18/11", received)
    assert follow.operation == date(2026, 11, 17)
    assert follow.needs_confirmation is False
    assert other.operation == date(2026, 11, 18)
    assert other.needs_confirmation is False
    assert read_operation_date("sem data aqui", received).needs_confirmation is True


def test_comandos() -> None:
    today = date(2026, 11, 17)
    fuel = parse_command("/ajustar combustivel=80 data=18/11", today)
    pnr = parse_command("/pnr 30,00", today)
    maintenance = parse_command('/manutencao "Troca de Óleo" 200,00', today)
    assert isinstance(fuel, FuelCommand)
    assert fuel.amount == Decimal("80.00")
    assert fuel.operation == date(2026, 11, 18)
    assert isinstance(pnr, PnrCommand)
    assert pnr.amount == Decimal("30.00")
    assert isinstance(maintenance, MaintenanceCommand)
    assert maintenance.description == "Troca de Óleo"
    assert maintenance.amount == Decimal("200.00")


def test_resposta_do_douglas_so_publica_no_controle() -> None:
    store = Store(None)
    outbound = RecordingOutbound()
    client = client_for(store, outbound)
    operation = date(2026, 11, 17)
    record = store.ensure_day(operation, Decimal("90"))
    record["routes"] = [{"code": "D9_PM1", "cities": ["Congonhinhas"], "shared": False}]
    record["stops_asked"] = True
    store.put_day(operation, record)

    response = client.post(
        "/webhooks/evolution",
        headers={"apikey": SECRET},
        json={
            "event": "messages.upsert",
            "data": {
                "key": {"remoteJid": "5565999607901@s.whatsapp.net", "fromMe": False, "id": "D1"},
                "message": {"conversation": "35"},
            },
        },
    )
    assert response.status_code == 200
    assert [item[0] for item in outbound.sent] == [CONTROL]
    text = outbound.sent[0][1]
    assert "R$ 260,00" in text
    assert "R$ 12,25" in text
    assert "R$ 100,00" in text
    assert "R$ 90,00" in text
    assert "R$ 87,25" in text
    assert DRIVER not in text

    client.post(
        "/webhooks/evolution",
        headers={"apikey": SECRET},
        json={
            "event": "messages.upsert",
            "data": {
                "key": {"remoteJid": "5565999607901@s.whatsapp.net", "fromMe": False, "id": "D2"},
                "message": {"conversation": "pode repetir?"},
            },
        },
    )
    assert len(outbound.sent) == 1


def test_pnr_nao_vai_para_o_grupo_de_origem() -> None:
    store = Store(None)
    outbound = RecordingOutbound()
    client = client_for(store, outbound)
    moment = datetime(2026, 11, 17, 16, 0, tzinfo=timezone.utc)
    client.app.state.service.handle(
        {
            "event": "messages.upsert",
            "data": {
                "key": {"remoteJid": CONTROL, "fromMe": False, "id": "C1", "participant": "5511999999999@s.whatsapp.net"},
                "message": {"conversation": "/pnr 30,00"},
            },
        },
        now=moment,
    )
    assert outbound.sent[0][0] == CONTROL
    assert "R$ 30,00" in outbound.sent[0][1]
    assert all(item[0] != ORIGIN for item in outbound.sent)
    assert all(item[0] != DRIVER for item in outbound.sent)


def test_fechamento_da_quinzena_envia_os_dois_relatorios() -> None:
    store = Store(None)
    outbound = RecordingOutbound()
    app = client_for(store, outbound)
    operation = date(2026, 11, 17)
    record = store.ensure_day(operation, Decimal("90"))
    record["routes"] = [{"code": "D9_PM1", "cities": ["Congonhinhas"], "shared": False}]
    record["stops"] = 35
    store.put_day(operation, record)
    app.app.state.service.tick(datetime(2026, 11, 30, 17, 0, tzinfo=SAO_PAULO))
    destinations = [item[0] for item in outbound.sent]
    assert DRIVER in destinations
    assert CONTROL in destinations
    assert ORIGIN not in destinations
    douglas = next(text for number, text in outbound.sent if number == DRIVER)
    fiorino = next(text for number, text in outbound.sent if number == CONTROL)
    assert "16/11 · sem rota" in douglas
    assert "30/11 · sem rota" in douglas
    assert "*Total a receber · R$ 100,00*" in douglas
    assert "*Lucro da quinzena · R$ 87,25*" in fiorino
