"""Lê a escala pelo texto do OCR. O modelo não vê a foto."""

import logging
import re
import unicodedata

from frota_plus.parana import CIDADES

logger = logging.getLogger("frota_plus.ocr")

_ROUTE = re.compile(r"(.+?)PM(\d+)$", re.IGNORECASE)
_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
_HEADERS = {"motorista", "rota", "cidade"}
_ENGINE = None


def _fold(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text)
    plain = "".join(char for char in plain if not unicodedata.combining(char))
    return "".join(char for char in plain.casefold() if char.isalnum())


_CITY = {_fold(name): name for name in CIDADES}


def valida_cidade(text: str) -> bool:
    return _fold(text) in _CITY


def nome_cidade(text: str) -> str | None:
    return _CITY.get(_fold(text))


def codigo_rota(text: str) -> str | None:
    compact = re.sub(r"[\s_]+", "", text)
    match = _ROUTE.fullmatch(compact)
    if match is None or not any(char.isalpha() for char in match.group(1)):
        return None
    return f"{match.group(1)}_PM{match.group(2)}"


def _menciona(text: str, driver_name: str) -> tuple[bool, bool]:
    driver = _fold(driver_name)
    words = [_fold(word) for word in _WORD.findall(text)]
    if driver not in words:
        return False, False
    others = [word for word in words if word not in {driver, "e"}]
    return True, bool(others)


def _fragmento(text: str, previous: str) -> bool:
    folded = _fold(text)
    return len(folded) >= 4 and _fold(previous).endswith(folded) and folded != _fold(previous)


def blocos(lines: list[str], driver_name: str) -> list[dict]:
    rows = [line.strip() for line in lines if line.strip()]
    routes: list[dict] = []
    index = 0
    while index < len(rows):
        line = rows[index]
        if _fold(line) in _HEADERS or _fold(line) == "ambulancia":
            index += 1
            continue
        present, shared = _menciona(line, driver_name)
        if not present or valida_cidade(line) or codigo_rota(line):
            index += 1
            continue
        index += 1
        code = None
        cities: list[str] = []
        while index < len(rows):
            current = rows[index]
            if _fold(current) in _HEADERS:
                index += 1
                continue
            if code is None and (found := codigo_rota(current)):
                code = found
                index += 1
                continue
            city = nome_cidade(current)
            if city:
                cities.append(city)
                index += 1
                continue
            if cities and _fragmento(current, cities[-1]):
                index += 1
                continue
            break
        if code:
            routes.append({"code": code, "cities": cities, "shared": shared})
    return routes


def _rapid_lines(image: bytes) -> list[str]:
    global _ENGINE
    if _ENGINE is None:
        from rapidocr_onnxruntime import RapidOCR

        _ENGINE = RapidOCR()
    result, _elapsed = _ENGINE(image)
    if not result:
        return []
    return [str(item[1]).strip() for item in result if str(item[1]).strip()]


class OcrScaleReader:
    def __init__(self, recognize=None) -> None:
        self._recognize = recognize or _rapid_lines

    def read(self, caption: str, image_jpeg: bytes | None, driver_name: str) -> dict:
        if not image_jpeg:
            logger.info("leitura_sem_arquivo")
            return {"confident": False, "routes": [], "status": "unconfident"}
        try:
            lines = self._recognize(image_jpeg)
        except Exception:
            logger.info("leitura_da_escala_falhou")
            return {"confident": False, "routes": [], "status": "error"}
        if not lines:
            logger.info("leitura_sem_confianca")
            return {"confident": False, "routes": [], "status": "unconfident"}
        routes = blocos(lines, driver_name)
        if not routes:
            logger.info("leitura_sem_motorista")
            return {"confident": True, "routes": [], "status": "absent"}
        logger.info("leitura_ok")
        return {"confident": True, "routes": routes, "status": "ok"}
