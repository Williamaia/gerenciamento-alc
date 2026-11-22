"""Dias já confirmados pelo administrador quando a leitura automática não gravou."""

from datetime import date
from decimal import Decimal

from frota_plus.store import Store

PUBLISHED_MESSAGE = {
    date(2026, 11, 18): "3EB05588CA2AA923C70076",
}

CONFIRMED_DAYS: dict[date, list[dict]] = {
    date(2026, 11, 18): [
        {
            "code": "C25_PM1",
            "cities": [
                "Abatiá",
                "Ribeirão do Pinhal",
                "Jundiaí do Sul",
                "Nova Fátima",
                "Congonhinhas",
            ],
            "shared": False,
        }
    ],
}


def apply_confirmed_days(store: Store, fuel: Decimal) -> None:
    for operation, routes in CONFIRMED_DAYS.items():
        record = store.ensure_day(operation, fuel)
        if not record.get("routes"):
            record["routes"] = routes
        if record.get("stops_fix") != "admin-30":
            record["stops"] = 30
            record["stops_asked"] = True
            record["stops_fix"] = "admin-30"
        if record.get("km_method") != "chain":
            record["km_ida"] = None
            record["km_volta"] = None
            record["km_method"] = "pending-chain"
        if not record.get("control_message_id"):
            record["control_message_id"] = PUBLISHED_MESSAGE.get(operation)
        record["awaiting_read"] = False
        store.put_day(operation, record)


def drop_foreign_route(store: Store) -> None:
    """A leitura de 22/11 atribuiu a B25_PM1 a quem não estava na escala."""
    operation = date(2026, 11, 22)
    record = store.day(operation)
    if not record or record.get("stops") is not None:
        return
    codes = [str(route.get("code") or "") for route in record.get("routes") or []]
    if codes != ["B25_PM1"]:
        return
    record["routes"] = []
    record["stops_asked"] = False
    record["stops_reminded"] = False
    store.put_day(operation, record)
