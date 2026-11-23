from datetime import datetime
from decimal import Decimal

from frota_plus.config import Settings
from frota_plus.domain.dates import SAO_PAULO
from frota_plus.domain.money import driver_pay
from frota_plus.main import create_app
from frota_plus.outbound import RecordingOutbound
from frota_plus.parana import CIDADES
from frota_plus.scale_ocr import OcrScaleReader, blocos, valida_cidade
from frota_plus.store import Store

ORIGIN = "origem@g.us"
CONTROL = "controle@g.us"
AUDIT = "audit@g.us"
DRIVER = "556599607901"
NIGHT = datetime(2026, 11, 21, 23, 9, tzinfo=SAO_PAULO)
DAY = NIGHT.date().replace(day=22)


class FetchOutbound(RecordingOutbound):
    def fetch_image(self, key: dict) -> bytes | None:
        return b"foto"


def build(lines: list[str]):
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
        ai_api_key="chave-que-nao-pode-ser-usada",
    )
    outbound = FetchOutbound()
    reader = OcrScaleReader(recognize=lambda _image: lines)
    app = create_app(settings, outbound=outbound, interpreter=reader, store=Store(None))
    return app, outbound


def scale() -> dict:
    return {
        "event": "messages.upsert",
        "data": {
            "key": {"remoteJid": ORIGIN, "fromMe": False, "id": "ESC"},
            "message": {"imageMessage": {"caption": "*Segue a escala 22/11*"}},
            "messageType": "imageMessage",
        },
    }


def test_valida_cidade_usa_os_municipios_do_parana() -> None:
    assert len(CIDADES) == 399
    assert valida_cidade("Douglas") is False
    assert valida_cidade("Nikolas") is False
    assert valida_cidade("Congonhinhas") is True
    assert valida_cidade("Nova Fatima") is True


def test_bloco_do_douglas_fecha_na_linha_que_nao_e_cidade() -> None:
    routes = blocos(
        ["Douglas", "exemplo_PM1", "Congonhinhas", "Nova Fatima", "Nikolas"],
        "Douglas",
    )
    assert routes == [
        {
            "code": "exemplo_PM1",
            "cities": ["Congonhinhas", "Nova Fátima"],
            "shared": False,
        }
    ]


def test_duas_aparicoes_sao_duas_rotas_completas() -> None:
    routes = blocos(
        [
            "Douglas",
            "A1_PM1",
            "Congonhinhas",
            "Outra Pessoa",
            "Douglas",
            "B2_PM1",
            "Nova Fatima",
            "Fim",
        ],
        "Douglas",
    )
    assert [route["shared"] for route in routes] == [False, False]
    assert driver_pay(2, 0) == Decimal("200.00")


def test_linha_com_outra_pessoa_e_rota_compartilhada() -> None:
    routes = blocos(
        ["Maria e Douglas", "C3_PM1", "Jacarezinho", "Pedro"],
        "Douglas",
    )
    assert len(routes) == 1
    assert routes[0]["shared"] is True
    assert routes[0]["code"] == "C3_PM1"
    assert routes[0]["cities"] == ["Jacarezinho"]
    assert driver_pay(0, 1) == Decimal("50.00")


def test_tabela_sem_douglas_nao_chama_modelo_nem_envia(monkeypatch) -> None:
    def fail(*_args, **_kwargs):
        raise AssertionError("o modelo foi chamado")

    monkeypatch.setattr("urllib.request.urlopen", fail)
    app, outbound = build(["Renan", "A10_PM1", "Abatia", "Santa Amelia"])
    app.state.service.handle(scale(), now=NIGHT)
    assert [text for number, text in outbound.sent if number == DRIVER] == []
    assert app.state.store.day(DAY)["routes"] == []
    notice = [text for number, text in outbound.sent if number == AUDIT][-1]
    assert "não escalado" in notice
    assert "/retry" not in notice
    assert "endpoint" not in notice


def test_ocr_sem_texto_fica_sem_confianca(monkeypatch) -> None:
    def fail(*_args, **_kwargs):
        raise AssertionError("o modelo foi chamado")

    monkeypatch.setattr("urllib.request.urlopen", fail)
    app, outbound = build([])
    app.state.service.handle(scale(), now=NIGHT)
    notice = [text for number, text in outbound.sent if number == AUDIT][-1]
    assert "não foi lida com segurança" in notice
    assert "/retry" in notice
    assert "endpoint" not in notice
    assert app.state.store.day(DAY) is None
