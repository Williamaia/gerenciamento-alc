# Design

## Context

As specs de `whatsapp-integration` e `security-and-permissions` já exigem webhook autenticado, sem segredo no código e sem efeito financeiro vindo de evento inválido. A Evolution API 2 envia JSON com `event`, `instance` e `data`, e pode incluir `apikey` no corpo. O cabeçalho de autenticação é configurável no webhook da Evolution.

## Goals / Non-Goals

**Goals:**

- Publicar um caminho estável para colar na Evolution.
- Validar o segredo por `Authorization: Bearer` ou pelo cabeçalho `apikey`.
- Responder sem criar pagamento e sem devolver segredo.

**Non-Goals:**

- Interpretar imagem, calcular rota ou falar com o modelo nesta change.
- Substituir o PostgreSQL por outro banco oficial.
- Abrir túnel público automaticamente.

## Decisions

- Python 3.12+ com FastAPI. O caminho é `POST /webhooks/evolution`.
- `GET /health` mostra o caminho e a URL montada com `PUBLIC_BASE_URL`, ou `http://127.0.0.1:<porta>/webhooks/evolution` quando a base pública não existe.
- Sem `EVOLUTION_WEBHOOK_SECRET`, o webhook responde 503. Segredo diferente responde 401. A comparação usa hash, para não vazar o valor.
- A chave do agente entra só por `AI_API_KEY` no ambiente. Ela não aparece em log, resposta ou arquivo versionado.
- O corpo da Evolution pode trazer `apikey`. Esse campo é descartado antes de qualquer registro.
- Identificador da mensagem, quando existir em `data.key.id`, deduplica na memória do processo.

## Risks / Trade-offs

- [Reinício perde a deduplicação em memória] → A próxima change grava o identificador no PostgreSQL.
- [127.0.0.1 não é alcançado pela Evolution em outro servidor] → A URL definitiva usa o domínio ou IP público em `PUBLIC_BASE_URL`.
- [O gerenciador da Evolution pode não ter campo de cabeçalho] → O segredo é enviado pelo `headers` da configuração do webhook, como `Authorization` ou `apikey`.
