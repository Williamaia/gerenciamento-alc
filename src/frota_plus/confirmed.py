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
