"""Quilometragem rodoviária na ordem da escala.

A ida segue de cidade em cidade. A volta sai só da última. O trecho medido fica guardado.
"""

import json
import logging
import time
import urllib.parse
import urllib.request
from decimal import Decimal, ROUND_HALF_UP

from frota_plus.domain.distance import SHED, known_between, normalize_city, route_distance
from frota_plus.store import Store

logger = logging.getLogger("frota_plus.routing")
USER_AGENT = "FrotaPlus/0.1 (gerenciamento operacional)"


class DistanceBook:
    def __init__(self, store: Store, fetch=None) -> None:
        self.store = store
        self.fetch = fetch

    def for_routes(self, routes: list[dict]) -> tuple[Decimal, Decimal] | None:
        return route_distance(routes, self.between)

    def between(self, start: str, end: str) -> Decimal | None:
        known = known_between(start, end)
        if known is not None:
            logger.info("km_medido")
            return known
        key = f"{normalize_city(start)}>{normalize_city(end)}"
        cached = self.store.distances.get(key)
        if isinstance(cached, dict) and cached.get("km"):
            logger.info("km_medido")
            return Decimal(cached["km"])
        if self.fetch is None:
            return None
        try:
            found = self.fetch(start, end)
        except Exception:
            logger.info("km_nao_encontrado")
            return None
        if found is None:
            logger.info("km_nao_encontrado")
            return None
        logger.info("km_medido")
        self.store.distances[key] = {"km": str(found)}
        self.store.save()
        return found


def fetch_road_leg(start: str, end: str) -> Decimal | None:
    origin = _geocode(_place(start))
    destination = _geocode(_place(end))
    if origin is None or destination is None:
        return None
    return _drive_km(origin, destination)


def _place(name: str) -> str:
    if normalize_city(name) == normalize_city(SHED):
        return f"{SHED}, Paraná, Brasil"
    return f"{name}, Paraná, Brasil"


_GEOCODE_CACHE: dict[str, tuple[str, str] | None] = {}


def _geocode(query: str) -> tuple[str, str] | None:
    if query in _GEOCODE_CACHE:
        return _GEOCODE_CACHE[query]
    time.sleep(1.1)
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
        _GEOCODE_CACHE[query] = None
        return None
    if not payload:
        _GEOCODE_CACHE[query] = None
        return None
    point = (str(payload[0]["lat"]), str(payload[0]["lon"]))
    _GEOCODE_CACHE[query] = point
    return point


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
