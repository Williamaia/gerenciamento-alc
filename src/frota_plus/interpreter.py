"""Leitura da escala. Data e valores oficiais não nascem aqui."""

import base64
import json
import logging
import urllib.request
from typing import Protocol

logger = logging.getLogger("frota_plus.interpreter")


class ScaleInterpreter(Protocol):
    def read(self, caption: str, image_jpeg: bytes | None, driver_name: str) -> dict: ...


class OpenAIInterpreter:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model or "gpt-4o-mini"

    def read(self, caption: str, image_jpeg: bytes | None, driver_name: str) -> dict:
        if not self.api_key or not image_jpeg:
            return {"confident": False, "routes": []}
        encoded = base64.b64encode(image_jpeg).decode("ascii")
        prompt = (
            "Leia a tabela da escala. Responda só JSON com as chaves confident e routes. "
            f"routes contém apenas as linhas em que o nome {driver_name} está na coluna do motorista. "
            "Cada rota tem code, cities (lista) e shared. "
            "shared=true somente quando o nome está na mesma célula que outra pessoa. "
            "Cidades nas linhas seguintes, sem outro motorista e sem outro código, pertencem a essa mesma rota. "
            "Texto em vermelho no formato 'Fulano apoiar rota' é ambulância: outra pessoa leva pacotes que não couberam. "
            "Não crie rota por causa dessa linha e não marque a rota do motorista como compartilhada. "
            "Se a imagem estiver ruim, confident=false e routes=[]. Não chute código, cidade nem nome."
        )
        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt + "\nTexto junto da imagem:\n" + (caption or "")},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}},
                    ],
                }
            ],
            "response_format": {"type": "json_object"},
        }
        call = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(call, timeout=60) as response:
                payload = json.loads(response.read().decode())
        except Exception:
            logger.info("leitura_da_escala_falhou")
            return {"confident": False, "routes": []}
        try:
            content = payload["choices"][0]["message"]["content"]
            parsed = json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            return {"confident": False, "routes": []}
        routes = []
        for item in parsed.get("routes") or []:
            if not isinstance(item, dict) or not item.get("code"):
                continue
            cities = [str(city) for city in item.get("cities") or [] if str(city).strip()]
            routes.append(
                {
                    "code": str(item["code"]).strip(),
                    "cities": cities,
                    "shared": bool(item.get("shared")),
                }
            )
        return {"confident": bool(parsed.get("confident")) and bool(routes), "routes": routes}
