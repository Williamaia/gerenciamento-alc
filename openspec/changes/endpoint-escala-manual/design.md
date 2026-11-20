# Design

## Context

O webhook só grava a escala que a Evolution entrega. O relógio das 08:00 pede paradas apenas para o dia que já tem rotas. Veja proposal.md para o caso da madrugada.

## Goals / Non-Goals

**Goals:**

- Receber data e rotas já lidas, gravar o dia e disparar o pedido de paradas com a regra de horário que já existe.
- Recusar credencial inválida, corpo incompleto e dia que já tem paradas.

**Non-Goals:**

- Não recuperar sozinho o histórico que a Evolution 2.3.7 não devolveu.
- Não ler imagem nem calcular quilometragem neste endpoint.
- Não enviar nada ao grupo de origem.

## Decisions

- O caminho é `POST /operacoes/escala`. O corpo usa `data` (`d/m` ou `d/m/aaaa`), `rotas` com `codigo`, `cidades` e `compartilhada`. Sem `compartilhada`, a rota é completa.
- A credencial é a mesma do webhook: `Authorization: Bearer` ou `apikey`, comparada com o segredo já configurado. Segredo vazio responde 503. Credencial errada responde 401.
- Data inválida ou rota sem código ou sem cidade responde 400 e não grava. Dia com paradas já preenchidas responde 409 e não altera o registro.
- A gravação reusa o dia operacional. Paradas ficam ausentes. Se a data é hoje e o horário local é 08:00 ou mais, e o pedido ainda não saiu, o envio formal ao motorista acontece na mesma chamada. Antes das 08:00, nada é enviado.

Alternativa descartada: um comando no grupo de controle. O caso real é a foto não ter chegado, então quem opera precisa informar a leitura fora do WhatsApp.

## Risks / Trade-offs

- [O mesmo segredo do webhook autoriza este endpoint] → ele já protege o webhook e não entra no repositório. Um segredo separado ficaria para outro change.
- [Um segundo envio antes da resposta do motorista] → se os códigos são os mesmos e o pedido já saiu, não manda de novo. Códigos diferentes substituem as rotas e pedem outra vez, porque o pedido anterior estaria errado.

## Migration Plan

- Implantar o endpoint e usá-lo para a escala que não entrou na Evolution.
- A versão anterior simplesmente não oferece o caminho. Nenhum dia já respondido é reescrito.
