# Proposal

## Why

O administrador escreveu `/ajuda` no grupo de controle e não recebeu resposta. O número conectado à Evolution é o dele, então o evento chega como mensagem própria e o comando nem é lido.

## What Changes

- `/ajuda` responde na mesma conversa autorizada com os comandos que o backend aceita hoje.
- A lista não anuncia comando que ainda não executa.
- Um comando do número conectado, no grupo de controle, deixa de ser descartado só porque a sessão marcou a mensagem como própria.
- O grupo de origem continua sem resposta.

## Capabilities

### New Capabilities

- Nenhuma.

### Modified Capabilities

- `whatsapp-commands`: a ajuda passa a listar combustível, manutenção, PNR e ajuda, e o comando do número conectado no grupo de controle é aceito.

## Impact

- Leitura do comando e o texto enviado de volta.
- Nenhum valor, parada ou rota é alterado pela ajuda.
