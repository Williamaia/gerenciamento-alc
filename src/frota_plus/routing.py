"""Quilometragem rodoviária a partir de Santo Antônio da Platina.

A ida e a volta são consultadas separadas. O resultado fica guardado para não mudar sozinho.
"""

import json
import logging
import urllib.parse
import urllib.request
from decimal import Decimal, ROUND_HALF_UP

from frota_plus.domain.distance import known_leg, normalize_city, sum_round_trips
from frota_plus.store import Store

logger = logging.getLogger("frota_plus.routing")
ORIGIN = "Santo Antônio da Platina, Paraná, Brasil"
USER_AGENT = "FrotaPlus/0.1 (gerenciamento operacional)"


class DistanceBook:
    def __init__(self, store: Store, fetch=None) -> None:
        self.store = store
        self.fetch = fetch

    def for_routes(self, routes: list[dict]) -> tuple[Decimal, Decimal] | None:
        return sum_round_trips(routes, self.leg)

    def leg(self, city: str) -> tuple[Decimal, Decimal] | None:
        known = known_leg(city)
        if known is not None:
            return known
        key = normalize_city(city)
        cached = self.store.distances.get(key)
        if isinstance(cached, dict) and cached.get("ida") and cached.get("volta"):
            return Decimal(cached["ida"]), Decimal(cached["volta"])
        if self.fetch is None:
            return None
        try:
            found = self.fetch(city)
        except Exception:
            logger.info("km_nao_encontrado")
            return None
        if found is None:
            return None
        self.store.distances[key] = {"ida": str(found[0]), "volta": str(found[1])}
        self.store.save()
        return found


def fetch_road_leg(city: str) -> tuple[Decimal, Decimal] | None:
    origin = _geocode(ORIGIN)
    destination = _geocode(f"{city}, Paraná, Brasil")
    if origin is None or destination is None:
        return None
    outbound = _drive_km(origin, destination)
    inbound = _drive_km(destination, origin)
    if outbound is None or inbound is None:
        return None
    return outbound, inbound


def _geocode(query: str) -> tuple[str, str] | None:
    params = urllib.parse.urlencode({"q": query, "format": "jsonv2", "limit": "1"})
    call = urllib.request.Request(
        f"https://nominatim.openstreetmap.org/search?{params}",
        headers={"User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(call, timeout=20) as response:
            payload = json.loads(response.read().decode())
    except Exception:
        logger.info("geocode_falhou")
        return None
    if not payload:
        return None
    return str(payload[0]["lat"]), str(payload[0]["lon"])


def _drive_km(start: tuple[str, str], end: tuple[str, str]) -> Decimal | None:
    path = f"{start[1]},{start[0]};{end[1]},{end[0]}"
    url = f"https://router.project-osrm.org/route/v1/driving/{path}?overview=false"
    call = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(call, timeout=20) as response:
            payload = json.loads(response.read().decode())
    except Exception:
        logger.info("rota_falhou")
        return None
    routes = payload.get("routes") if isinstance(payload, dict) else None
    if not routes:
        return None
    meters = Decimal(str(routes[0]["distance"]))
    return (meters / Decimal("1000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
