"""Distância do caminho: ida até a última cidade e volta só de lá."""

import unicodedata
from decimal import Decimal

SHED = "Santo Antônio da Platina"

# Ida e volta já conferidas entre o barracão e a cidade. Não vale para o trecho entre duas cidades.
ONE_WAY_KM: dict[str, tuple[Decimal, Decimal]] = {
    "congonhinhas": (Decimal("73"), Decimal("73")),
}


def normalize_city(name: str) -> str:
    decomposed = unicodedata.normalize("NFD", name.strip().casefold())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def known_between(start: str, end: str) -> Decimal | None:
    start_key = normalize_city(start)
    end_key = normalize_city(end)
    shed = normalize_city(SHED)
    if start_key == shed:
        pair = ONE_WAY_KM.get(end_key)
        return pair[0] if pair else None
    if end_key == shed:
        pair = ONE_WAY_KM.get(start_key)
        return pair[1] if pair else None
    return None


def route_distance(routes: list[dict], km_between) -> tuple[Decimal, Decimal] | None:
    """Ida na ordem da escala e volta só da última cidade. Um trecho faltante deixa o dia pendente."""
    outbound = Decimal("0")
    inbound = Decimal("0")
    found = False
    for route in routes:
        cities = [str(city).strip() for city in route.get("cities") or [] if str(city).strip()]
        if not cities:
            return None
        points = [SHED, *cities]
        for start, end in zip(points, points[1:]):
            leg = km_between(start, end)
            if leg is None:
                return None
            outbound += leg
            found = True
        back = km_between(cities[-1], SHED)
        if back is None:
            return None
        inbound += back
    if not found:
        return None
    return outbound, inbound
