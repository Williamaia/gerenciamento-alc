# Proposal

## Why

A escala pode chegar de madrugada no grupo dos motoristas e não entrar na sessão da Evolution. Sem a foto no webhook, o pedido das 08:00 não sai, e reenviar a imagem no grupo nem sempre é possível.

## What Changes

- Um endpoint autenticado recebe a escala já lida: data, código de cada rota, cidades na ordem e se a rota é compartilhada.
- O backend grava essas rotas como escala confirmada, sem chamar leitura de imagem e sem inventar parada, quilometragem ou valor.
- Se a data é hoje e já passou das 08:00, o pedido formal de paradas sai na hora. Antes das 08:00, o relógio existente faz o pedido.
- Dia que já tem paradas respondidas não é sobrescrito.
- Quando a Evolution não recupera o intervalo perdido, o aviso ao administrador aponta esse endpoint como o registro manual.

## Capabilities

### New Capabilities

- `escala-manual`: registro autenticado de uma escala que não chegou pelo WhatsApp, com as rotas informadas e o mesmo fluxo de paradas do dia.

### Modified Capabilities

- `whatsapp-integration`: a lacuna sem recuperação de histórico deixa de terminar só no aviso. O administrador registra a escala pelo endpoint, e o sistema continua sem inventar o que não foi informado.

## Impact

- Novo `POST` no serviço HTTP, com o mesmo segredo do webhook.
- Memória do dia e o pedido de paradas ao motorista.
- Nenhum envio no grupo de origem. O parecer do grupo de controle só sai depois da quantidade de paradas, como hoje.
