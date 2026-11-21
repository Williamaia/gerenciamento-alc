"""Envio para a Evolution. O grupo de origem nunca é destino."""

import base64
import json
import logging
import urllib.error
import urllib.request
from typing import Protocol

logger = logging.getLogger("frota_plus.outbound")


class Outbound(Protocol):
    def send_text(self, number: str, text: str) -> str | None: ...

    def edit_text(self, number: str, message_id: str, text: str) -> None: ...


class RecordingOutbound:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []
        self.edited: list[tuple[str, str, str]] = []

    def send_text(self, number: str, text: str) -> str | None:
        self.sent.append((number, text))
        return f"local-{len(self.sent)}"

    def edit_text(self, number: str, message_id: str, text: str) -> None:
        self.edited.append((number, message_id, text))


class EvolutionOutbound:
    def __init__(self, base_url: str, api_key: str, instance: str, on_http_error=None) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.instance = instance
        self.on_http_error = on_http_error
        self._reporting = False

    def send_text(self, number: str, text: str) -> str | None:
        if not self.base_url or not self.api_key or not self.instance:
            logger.info("envio_ignorado destino_sem_api")
            return None
        logger.info("envio_texto")
        payload = self._request(
            "POST",
            f"/message/sendText/{self.instance}",
            {"number": number, "text": text},
        )
        key = payload.get("key") if isinstance(payload, dict) else None
        if isinstance(key, dict) and key.get("id"):
            return str(key["id"])
        return None

    def fetch_image(self, key: dict) -> bytes | None:
        if not self.base_url or not self.api_key or not self.instance:
            return None
        payload = self._request(
            "POST",
            f"/chat/getBase64FromMediaMessage/{self.instance}",
            {"message": {"key": key}, "convertToMp4": False},
        )
        raw = payload.get("base64") if isinstance(payload, dict) else None
        if not isinstance(raw, str) or not raw:
            return None
        if raw.startswith("data:"):
            raw = raw.split(",", 1)[1]
        try:
            return base64.b64decode(raw)
        except Exception:
            return None

    def edit_text(self, number: str, message_id: str, text: str) -> None:
        if not self.base_url or not self.api_key or not self.instance:
            return
        self._request(
            "POST",
            f"/chat/updateMessage/{self.instance}",
            {
                "number": number,
                "text": text,
                "key": {"remoteJid": number, "fromMe": True, "id": message_id},
            },
        )

    def _request(self, method: str, path: str, body: dict) -> dict:
        call = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(body).encode(),
            headers={"apikey": self.api_key, "Content-Type": "application/json"},
            method=method,
        )
        try:
            with urllib.request.urlopen(call, timeout=30) as response:
                raw = response.read().decode()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as error:
            logger.info("evolution_http status=%s path=%s", error.code, path)
            self._report_http_error(error.code, path)
            return {}

    def _report_http_error(self, status: int, path: str) -> None:
        if self._reporting or self.on_http_error is None:
            return
        self._reporting = True
        try:
            self.on_http_error(status, path)
        finally:
            self._reporting = False
