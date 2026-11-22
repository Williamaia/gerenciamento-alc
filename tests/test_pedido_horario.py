from datetime import datetime
from decimal import Decimal

from frota_plus.confirmed import drop_foreign_route
from frota_plus.config import Settings
from frota_plus.domain.dates import SAO_PAULO
from frota_plus.main import create_app
from frota_plus.outbound import RecordingOutbound
from frota_plus.store import Store

ORIGIN = "origem@g.us"
CONTROL = "controle@g.us"
AUDIT = "audit@g.us"
DRIVER = "556599607901"
NIGHT = datetime(2026, 11, 21, 23, 9, tzinfo=SAO_PAULO)
EARLY = datetime(2026, 11, 22, 4, 30, tzinfo=SAO_PAULO)
MORNING = datetime(2026, 11, 22, 8, 0, tzinfo=SAO_PAULO)
TEN = datetime(2026, 11, 22, 10, 0, tzinfo=SAO_PAULO)
ROUTE = {
    "confident": True,
    "status": "ok",
    "routes": [{"code": "A12_PM1", "cities": ["Nova Fátima"], "shared": False}],
}
ABSENT = {"confident": True, "status": "absent", "routes": []}


class ScriptInterpreter:
    def __init__(self, results: list[dict]) -> None:
        self.results = list(results)
        self.calls = 0

    def read(self, caption: str, image_jpeg: bytes | None, driver_name: str) -> dict:
        self.calls += 1
        return self.results.pop(0)


class FetchOutbound(RecordingOutbound):
    def fetch_image(self, key: dict) -> bytes | None:
        return b"foto"


def build(interpreter, store: Store | None = None):
    settings = Settings(
        evolution_webhook_secret="segredo-de-teste",
        whatsapp_origin_group_id=ORIGIN,
        whatsapp_control_group_id=CONTROL,
        whatsapp_audit_group_id=AUDIT,
        whatsapp_driver_number=DRIVER,
        fuel_daily_amount="90",
        data_path="",
        evolution_api_base_url="",
        evolution_api_key="",
        evolution_instance="",
        ai_api_key="",
    )
    outbound = FetchOutbound()
    app = create_app(settings, outbound=outbound, interpreter=interpreter, store=store or Store(None))
    return app, app.state.store, outbound


def scale(caption: str) -> dict:
    return {
        "event": "messages.upsert",
        "data": {
            "key": {"remoteJid": ORIGIN, "fromMe": False, "id": "ESC"},
            "message": {"imageMessage": {"caption": caption}},
            "messageType": "imageMessage",
        },
    }


def to_driver(outbound: RecordingOutbound) -> list[str]:
    return [text for number, text in outbound.sent if number == DRIVER]


def test_escala_de_noite_nao_pede_paradas() -> None:
    app, store, outbound = build(ScriptInterpreter([ROUTE]))
    app.state.service.handle(scale("*Segue a escala 22/11*"), now=NIGHT)
    assert to_driver(outbound) == []
    assert store.day(MORNING.date())["routes"][0]["code"] == "A12_PM1"
    assert store.day(MORNING.date())["stops_asked"] is False


def test_escala_ate_as_cinco_nao_pede_paradas() -> None:
    app, store, outbound = build(ScriptInterpreter([ROUTE]))
    app.state.service.handle(scale("*Segue a escala 22/11*"), now=EARLY)
    assert to_driver(outbound) == []
    assert store.day(MORNING.date())["stops_asked"] is False


def test_relogio_das_oito_pede_uma_vez() -> None:
    app, store, outbound = build(ScriptInterpreter([ROUTE]))
    app.state.service.handle(scale("*Segue a escala 22/11*"), now=EARLY)
    app.state.service.tick(MORNING)
    messages = to_driver(outbound)
    assert len(messages) == 1
    assert "A12_PM1" in messages[0]
    assert "Olá. Sou o agente da Frota Plus." in messages[0]
    app.state.service.tick(MORNING)
    assert len(to_driver(outbound)) == 1
    assert store.day(MORNING.date())["stops_asked"] is True


def test_sem_nome_nao_envia_nada_ao_motorista() -> None:
    app, store, outbound = build(ScriptInterpreter([ABSENT]))
    app.state.service.handle(scale("*Segue a escala 22/11*"), now=NIGHT)
    assert to_driver(outbound) == []
    day = store.day(MORNING.date())
    assert day["routes"] == []
    notice = [text for number, text in outbound.sent if number == AUDIT][-1]
    assert notice.startswith("✅")
    assert "não escalado" in notice
    assert "B25_PM1" not in notice
    assert "endpoint" not in notice
    assert "/retry" not in notice
    app.state.service.tick(MORNING)
    app.state.service.tick(TEN)
    assert to_driver(outbound) == []


def test_b25_gravada_nao_gera_pedido_nem_lembrete() -> None:
    store = Store(None)
    record = store.ensure_day(MORNING.date(), Decimal("90"))
    record["routes"] = [{"code": "B25_PM1", "cities": ["Nova Fátima"], "shared": False}]
    record["stops_asked"] = True
    store.put_day(MORNING.date(), record)
    app, stored, outbound = build(ScriptInterpreter([ABSENT]), store)
    assert stored.day(MORNING.date())["routes"] == []
    app.state.service.tick(MORNING)
    app.state.service.tick(TEN)
    assert to_driver(outbound) == []
    drop_foreign_route(stored)
    assert stored.day(MORNING.date())["routes"] == []
