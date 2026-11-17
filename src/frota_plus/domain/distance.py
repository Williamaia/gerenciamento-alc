"""Distâncias de ida e volta já conferidas, a partir de Santo Antônio da Platina."""

import unicodedata
from decimal import Decimal

# Quilometragem rodoviária entre as sedes. A volta fica explícita, mesmo quando igual.
ONE_WAY_KM: dict[str, tuple[Decimal, Decimal]] = {
    "congonhinhas": (Decimal("73"), Decimal("73")),
}


def normalize_city(name: str) -> str:
    decomposed = unicodedata.normalize("NFD", name.strip().casefold())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def known_leg(city: str) -> tuple[Decimal, Decimal] | None:
    return ONE_WAY_KM.get(normalize_city(city))


def sum_round_trips(routes: list[dict], leg_for) -> tuple[Decimal, Decimal] | None:
    """Soma a ida e a volta de cada cidade, em cada rota. Uma cidade sem km deixa o dia pendente."""
    outbound = Decimal("0")
    inbound = Decimal("0")
    found = False
    for route in routes:
        cities = route.get("cities") or []
        if not cities:
            return None
        for city in cities:
            leg = leg_for(city)
            if leg is None:
                return None
            found = True
            outbound += leg[0]
            inbound += leg[1]
    if not found:
        return None
    return outbound, inbound
