# Frota Plus

Gestão operacional e financeira de uma frota de Fiorinos, acionada pelo WhatsApp.

## Estado

O contrato continua em `openspec/specs/`. A primeira change em implementação é o webhook da Evolution: `openspec/changes/python-evolution-webhook`.

## Webhook da Evolution

Caminho fixo: `POST /webhooks/evolution`.

Enquanto o serviço roda nesta máquina, a URL local é:

`http://127.0.0.1:8000/webhooks/evolution`

Quando o Frota Plus estiver acessível pela internet, cadastre na Evolution:

`https://SEU_DOMINIO/webhooks/evolution`

Defina `PUBLIC_BASE_URL` com essa origem, sem barra no final. O `GET /health` devolve a URL montada. A Evolution, se estiver em outro servidor, não alcança `127.0.0.1`.

O mesmo valor de `EVOLUTION_WEBHOOK_SECRET` precisa ir no cabeçalho do webhook da Evolution, como `Authorization: Bearer ...` ou `apikey`. Sem esse segredo o endpoint responde 503 e não processa evento.

```text
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m frota_plus
```

A chave do agente fica somente no `.env`.

## Estrutura

- `openspec/specs/`: contrato de comportamento.
- `openspec/changes/python-evolution-webhook/`: change em andamento.
- `src/frota_plus/`: serviço Python.
- `tests/`: testes do webhook.
- `docs/fase-1-analise.md`: decisões da especificação.
- `.env.example`: nomes de configuração, sem segredos.

## O que o sistema deve fazer

O número conectado à Evolution API observa o grupo da ALC, interpreta imagens de escala e publica o controle no grupo autorizado. O PostgreSQL guarda o histórico. O pagamento do motorista segue rota completa e rota compartilhada. Paradas e quilometragem ficam separadas. O demonstrativo em PDF sai no dia 15 e no último dia do mês, às 17:00, em `America/Sao_Paulo`.
