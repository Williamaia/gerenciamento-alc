# Proposal

## Why

O pedido de paradas chega ao motorista como um aviso curto de sistema. Ele precisa parecer uma pessoa, deixar claro que a resposta é só a quantidade de paradas, e cobrar de novo às 10:00 quando essa quantidade ainda não chegou.

## What Changes

- A mensagem das 08:00 passa a ser formal, em primeira pessoa, identificando o remetente como agente da Frota Plus.
- A mensagem lista o código de cada rota do dia e pede somente a quantidade de paradas, sem quantidade de pacotes.
- **BREAKING**: o texto deixa de ser `frota-plus-agent` seguido de `Quantas paradas em cada rota?`.
- Se a quantidade continuar ausente às 10:00 em America/Sao_Paulo, o agente envia um único lembrete no mesmo dia. Fora isso, continua sem responder a conversa do motorista.
- A quantidade respondida continua sendo gravada, e o parecer do dia continua indo só ao grupo de controle.

## Capabilities

### New Capabilities

- Nenhuma.

### Modified Capabilities

- `ai-agent`: o pedido de paradas ao motorista muda o texto, a identificação e passa a permitir um lembrete único às 10:00.

## Impact

- Texto enviado no WhatsApp particular do motorista.
- Agenda do mesmo dia, às 08:00 e às 10:00, em America/Sao_Paulo.
- O grupo de origem permanece sem envio. O parecer do grupo de controle e o pagamento do motorista não mudam.
