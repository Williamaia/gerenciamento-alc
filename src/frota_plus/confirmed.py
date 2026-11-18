"""Dias já confirmados pelo administrador quando a leitura automática não gravou."""

from datetime import date
from decimal import Decimal

from frota_plus.store import Store

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
        current = store.day(operation)
        if current and current.get("routes"):
            continue
        record = store.ensure_day(operation, fuel)
        record["routes"] = routes
        record["awaiting_read"] = False
        store.put_day(operation, record)
