# Proposal

## Why

Às 23:09 de 21/11 o motorista recebeu pedido de paradas da rota B25_PM1. A escala era de 22/11 e ele não estava escalado. O pedido saiu na hora porque o relógio já passava das 08:00 do dia do recebimento.

## What Changes

- O pedido de paradas só sai na data da escala, a partir das 08:00 em America/Sao_Paulo.
- A escala chega na véspera ou no próprio dia, até as 05:00. Nesses horários nada é enviado ao motorista.
- Se a leitura não encontra o nome Douglas, ele não está escalado: nada é gravado para ele e nada é enviado.
- Quando ele tem rota, o pedido sai às 08:00, com o lembrete das 10:00 se a quantidade seguir ausente.

## Capabilities

### New Capabilities

- Nenhuma.

### Modified Capabilities

- `ai-agent`: o pedido de paradas fica preso à data da escala e às 08:00 dessa data.
- `image-processing`: rota sem o nome do motorista monitorado não é gravada para ele.

## Impact

- Leitura da escala e o momento do envio ao motorista.
- O parecer e o grupo de origem não mudam de destino.
