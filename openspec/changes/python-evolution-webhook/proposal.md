# Proposal

## Why

A Evolution API precisa de uma URL pública para entregar mensagens. O Frota Plus ainda não tinha serviço para receber esses eventos, e a chave do agente não pode ficar no código.

## What Changes

- Criar o serviço em Python com o caminho `POST /webhooks/evolution`.
- Recusar evento quando o segredo do webhook não estiver configurado ou não conferir.
- Não calcular pagamento nem gravar a chave do agente no repositório.
- Informar a URL operacional em `GET /health`.

## Capabilities

### New Capabilities

- Nenhuma. Esta change implementa o recebimento já descrito em `whatsapp-integration`.

### Modified Capabilities

- Nenhuma. O comportamento exigido não muda; `skip_specs` está marcado porque não há delta de spec.

## Impact

- Novo pacote Python em `src/frota_plus`.
- A URL a cadastrar na Evolution é a base pública mais `/webhooks/evolution`.
- A deduplicação desta etapa vale enquanto o processo estiver no ar. A persistência em PostgreSQL fica para a próxima change.
