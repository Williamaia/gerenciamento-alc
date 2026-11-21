import logging
from datetime import datetime
from decimal import Decimal

from frota_plus.config import Settings
from frota_plus.domain.dates import SAO_PAULO
from frota_plus.main import create_app
from frota_plus.outbound import RecordingOutbound
from frota_plus.routing import DistanceBook
from frota_plus.store import Store

SECRET = "segredo-de-teste"
ORIGIN = "origem@g.us"
CONTROL = "controle@g.us"
AUDIT = "audit@g.us"
DAWN = datetime(2026, 11, 21, 0, 40, tzinfo=SAO_PAULO)
GOOD = {
    "confident": True,
    "status": "ok",
    "routes": [{"code": "A12_PM1", "cities": ["Nova Fátima"], "shared": False}],
}
UNSURE = {"confident": False, "status": "unconfident", "routes": []}
READER_DOWN = {"confident": False, "status": "error", "routes": []}


class ScriptInterpreter:
    def __init__(self, results: list[dict]) -> None:
        self.results = list(results)
        self.calls: list[bytes | None] = []

    def read(self, caption: str, image_jpeg: bytes | None, driver_name: str) -> dict:
        self.calls.append(image_jpeg)
        return self.results.pop(0)


class FetchOutbound(RecordingOutbound):
    def __init__(self, image: bytes | None = b"foto") -> None:
        super().__init__()
        self.image = image
        self.keys: list[dict] = []

    def fetch_image(self, key: dict) -> bytes | None:
        self.keys.append(key)
        return self.image


def build(interpreter, outbound, audit: str = AUDIT):
    settings = Settings(
        evolution_webhook_secret=SECRET,
        whatsapp_origin_group_id=ORIGIN,
        whatsapp_control_group_id=CONTROL,
        whatsapp_audit_group_id=audit,
        whatsapp_driver_number="556599607901",
        fuel_daily_amount="90",
        data_path="",
        evolution_api_base_url="",
        evolution_api_key="",
        evolution_instance="",
        ai_api_key="",
    )
    store = Store(None)
    app = create_app(settings, outbound=outbound, interpreter=interpreter, store=store)
    return app, store, outbound


def scale(caption: str, message_id: str = "F1", from_me: bool = False, remote: str = ORIGIN) -> dict:
    return {
        "event": "messages.upsert",
        "data": {
            "key": {"remoteJid": remote, "fromMe": from_me, "id": message_id},
            "message": {"imageMessage": {"caption": caption}},
            "messageType": "imageMessage",
        },
    }


def command(text: str, remote: str = CONTROL, from_me: bool = False) -> dict:
    return {
        "event": "messages.upsert",
        "data": {
            "key": {"remoteJid": remote, "fromMe": from_me, "id": "C-" + text},
            "message": {"conversation": text},
        },
    }


def audits(outbound: RecordingOutbound) -> list[str]:
    return [text for number, text in outbound.sent if number == AUDIT]


def controls(outbound: RecordingOutbound) -> list[str]:
    return [text for number, text in outbound.sent if number == CONTROL]


def test_ajuda_do_numero_conectado_nao_mexe_no_dia() -> None:
    app, store, outbound = build(ScriptInterpreter([GOOD]), FetchOutbound())
    before = dict(store.days)
    app.state.service.handle(command("/ajuda", from_me=True), now=DAWN)
    text = controls(outbound)[0]
    assert "combustivel" in text.casefold()
    assert "manutencao" in text.casefold() or "manutenção" in text.casefold()
    assert "/pnr" in text
    assert "/ajuda" in text
    assert "calculados pelo sistema" in text
    assert store.days == before
    assert all(number != ORIGIN for number, _ in outbound.sent)
    assert app.state.interpreter.calls == []


def test_foto_lida_avisa_sucesso_sem_chamar_o_modelo_de_novo(caplog) -> None:
    interpreter = ScriptInterpreter([GOOD])
    app, store, outbound = build(interpreter, FetchOutbound(b"foto-21"))
    with caplog.at_level(logging.INFO):
        app.state.service.handle(scale("*Segue escala 21/11*"), now=DAWN)
    assert interpreter.calls == [b"foto-21"]
    assert store.day(DAWN.date())["routes"][0]["code"] == "A12_PM1"
    assert store.day(DAWN.date())["stops"] is None
    notice = audits(outbound)[0]
    assert notice.startswith("✅ Frota Plus")
    assert "21/11/2026" in notice
    assert "A12_PM1" in notice
    assert "R$" not in notice
    assert controls(outbound) == []
    assert "leitura_inicio" in caplog.text
    assert "sk-" not in caplog.text


def test_foto_nao_baixada_pede_retry_e_nao_avisa_o_controle() -> None:
    interpreter = ScriptInterpreter([GOOD])
    app, store, outbound = build(interpreter, FetchOutbound(None))
    app.state.service.handle(scale("*Segue escala 21/11*"), now=DAWN)
    assert interpreter.calls == []
    assert store.day(DAWN.date()) is None
    assert store.pending_scale["key"]["id"] == "F1"
    notice = audits(outbound)[0]
    assert notice.startswith("❌ Frota Plus")
    assert "não foi baixada" in notice
    assert "/retry" in notice
    assert "endpoint" not in notice
    assert controls(outbound) == []
    assert all(number != ORIGIN for number, _ in outbound.sent)


def test_sem_grupo_de_auditoria_o_erro_nao_vai_ao_controle() -> None:
    app, store, outbound = build(ScriptInterpreter([GOOD]), FetchOutbound(None), audit="")
    app.state.service.handle(scale("*Segue escala 21/11*"), now=DAWN)
    assert outbound.sent == []
    assert store.pending_scale is not None


def test_leitor_que_nao_responde_pede_retry() -> None:
    interpreter = ScriptInterpreter([READER_DOWN])
    app, store, outbound = build(interpreter, FetchOutbound())
    app.state.service.handle(scale("*Segue escala 21/11*"), now=DAWN)
    assert interpreter.calls == [b"foto"]
    notice = audits(outbound)[0]
    assert "não terminou" in notice
    assert "/retry" in notice
    assert "endpoint" not in notice
    assert store.days == {}


def test_primeira_leitura_sem_confianca_pede_retry() -> None:
    interpreter = ScriptInterpreter([UNSURE])
    app, store, outbound = build(interpreter, FetchOutbound())
    app.state.service.handle(scale("*Segue escala 21/11*"), now=DAWN)
    notice = audits(outbound)[0]
    assert "não foi lida com segurança" in notice
    assert "/retry" in notice
    assert "endpoint" not in notice
    assert store.days == {}


def test_data_inutil_pede_endpoint_e_nao_chama_o_modelo() -> None:
    interpreter = ScriptInterpreter([GOOD])
    app, store, outbound = build(interpreter, FetchOutbound())
    app.state.service.handle(scale("*Segue a escala*"), now=DAWN)
    assert interpreter.calls == []
    notice = audits(outbound)[0]
    assert "não tem data utilizável" in notice
    assert "não resolve" in notice
    assert "endpoint manual" in notice
    assert store.days == {}


def test_retry_que_continua_sem_confianca_pede_endpoint() -> None:
    interpreter = ScriptInterpreter([UNSURE, UNSURE])
    app, store, outbound = build(interpreter, FetchOutbound())
    app.state.service.handle(scale("*Segue escala 21/11*"), now=DAWN)
    app.state.service.handle(command("/retry", from_me=True), now=DAWN)
    assert len(interpreter.calls) == 2
    notice = audits(outbound)[-1]
    assert "lida de novo" in notice
    assert "não é o caminho" in notice
    assert "endpoint manual" in notice
    assert store.days == {}
    assert controls(outbound) == []


def test_retry_recomeça_e_grava_a_leitura_nova() -> None:
    first = {"confident": False, "status": "unconfident", "routes": []}
    second = {
        "confident": True,
        "status": "ok",
        "routes": [{"code": "A12_PM1", "cities": ["Nova Fátima"], "shared": False}],
    }
    interpreter = ScriptInterpreter([first, second])
    outbound = FetchOutbound(b"foto-nova")
    app, store, _ = build(interpreter, outbound)
    app.state.service.handle(scale("*Segue escala 21/11*"), now=DAWN)
    app.state.service.handle(command("/retry", from_me=True), now=DAWN)
    assert interpreter.calls == [b"foto-nova", b"foto-nova"]
    assert len(outbound.keys) == 2
    day = store.day(DAWN.date())
    assert day["routes"][0]["code"] == "A12_PM1"
    assert day["stops"] is None
    assert store.pending_scale is None
    confirm = controls(outbound)[0]
    assert "21/11/2026" in confirm
    assert "A12_PM1" in confirm
    assert "R$" not in confirm
    assert audits(outbound)[-1].startswith("✅")
    assert all(number != ORIGIN for number, _ in outbound.sent)


def test_retry_sem_foto_nao_altera_o_dia() -> None:
    app, store, outbound = build(ScriptInterpreter([GOOD]), FetchOutbound())
    before = dict(store.days)
    app.state.service.handle(command("/retry"), now=DAWN)
    assert "Não há foto" in controls(outbound)[0]
    assert store.days == before
    assert app.state.interpreter.calls == []


def test_retry_nao_reescreve_dia_com_paradas() -> None:
    interpreter = ScriptInterpreter([GOOD])
    app, store, outbound = build(interpreter, FetchOutbound())
    record = store.ensure_day(DAWN.date(), Decimal("90"))
    record["routes"] = [{"code": "D9_PM1", "cities": ["Congonhinhas"], "shared": False}]
    record["stops"] = 30
    store.put_day(DAWN.date(), record)
    store.set_pending_scale({"key": {"id": "F9", "remoteJid": ORIGIN, "fromMe": False}, "text": "*Segue escala 21/11*"})
    app.state.service.handle(command("/retry", from_me=True), now=DAWN)
    assert store.day(DAWN.date())["stops"] == 30
    assert store.day(DAWN.date())["routes"][0]["code"] == "D9_PM1"
    assert interpreter.calls == []
    notice = audits(outbound)[0]
    assert "já tem paradas" in notice
    assert "endpoint" not in notice
    assert "Nada foi alterado" in controls(outbound)[0]


def test_retry_no_grupo_de_origem_nao_responde() -> None:
    outbound = FetchOutbound()
    app, store, _ = build(ScriptInterpreter([GOOD]), outbound)
    app.state.service.handle(command("/retry", remote=ORIGIN), now=DAWN)
    assert outbound.sent == []
    assert outbound.keys == []
    assert store.days == {}


def test_falha_de_envio_nao_aponta_retry_nem_endpoint() -> None:
    app, _, outbound = build(ScriptInterpreter([GOOD]), FetchOutbound())
    app.state.service.report_send_failure(500, "/message/sendText/alc")
    notice = audits(outbound)[0]
    assert notice.startswith("❌")
    assert "envio da mensagem falhou" in notice
    assert "não reenvia" in notice
    assert "endpoint" not in notice
    assert "apikey" not in notice.casefold()
    assert controls(outbound) == []
    assert app.state.interpreter.calls == []


def test_ciclo_vazio_nao_avisa_o_grupo(caplog) -> None:
    app, _, outbound = build(ScriptInterpreter([GOOD]), FetchOutbound())
    with caplog.at_level(logging.INFO):
        app.state.service.tick(datetime(2026, 11, 21, 7, 0, tzinfo=SAO_PAULO))
    assert audits(outbound) == []
    assert "agenda_sem_efeito" in caplog.text


def test_km_deixa_log(caplog) -> None:
    book = DistanceBook(Store(None))
    with caplog.at_level(logging.INFO):
        assert book.between("Santo Antônio da Platina", "Congonhinhas") == 73
    assert "km_medido" in caplog.text


def test_comando_no_grupo_de_auditoria_nao_altera_nada() -> None:
    interpreter = ScriptInterpreter([UNSURE])
    app, store, outbound = build(interpreter, FetchOutbound())
    app.state.service.handle(scale("*Segue escala 21/11*"), now=DAWN)
    sent = len(outbound.sent)
    app.state.service.handle(command("/retry", remote=AUDIT), now=DAWN)
    assert len(interpreter.calls) == 1
    assert store.days == {}
    assert len(outbound.sent) == sent
    assert all(number != ORIGIN for number, _ in outbound.sent)
