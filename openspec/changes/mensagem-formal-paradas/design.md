# Design

## Context

O pedido das 08:00 já sai pelo relógio interno, uma vez por dia, para o número do motorista. A resposta numérica é gravada e o parecer vai ao grupo de controle. Qualquer outra fala do motorista fica sem resposta. Veja proposal.md para o motivo da mudança.

## Goals / Non-Goals

**Goals:**

- Trocar o texto das 08:00 pelo cumprimento formal, com os códigos do dia e o aviso de que a resposta é só a quantidade de paradas.
- Enviar um lembrete único às 10:00 do mesmo dia quando a quantidade continuar ausente.
- Manter a captura do número e a publicação do parecer no grupo de controle.

**Non-Goals:**

- Não mudar a leitura da resposta numérica, o cálculo das paradas nem o texto do parecer.
- Não conversar com o motorista fora do pedido e do lembrete.
- Não enviar mensagem no grupo de origem.

## Decisions

- O texto fica fixo no relatório de saída. Os códigos entram um por linha, na ordem das rotas do dia. A saudação "Olá. Sou o agente da Frota Plus." substitui "frota-plus-agent".
- O lembrete repete a identificação e o aviso sobre pacotes, e troca o pedido por "Ainda não recebi a quantidade de paradas das seguintes rotas:".
- O mesmo laço que hoje acorda a cada 30 segundos passa a tratar dois horários: a partir das 08:00 pede as paradas; a partir das 10:00, no mesmo dia e só se o pedido já saiu e a quantidade segue vazia, envia o lembrete uma vez.
- Um marcador no dia impede o segundo lembrete. Resposta recebida antes das 10:00 não dispara lembrete.
- Se o processo voltar depois das 10:00 e ainda for o mesmo dia, o lembrete sai nessa volta. No dia seguinte, o dia anterior não é cobrado.

Alternativa descartada: repetir o lembrete em intervalos até a resposta. O pedido é um único aviso às 10:00.

## Risks / Trade-offs

- [O processo está desligado na passagem das 10:00 e só volta no dia seguinte] → o lembrete daquele dia não sai. O mesmo limite já vale para o pedido das 08:00 quando o dia vira.
- [A mensagem editada no grupo de controle de hoje não faz parte deste change] → este desenho só altera a conversa com o motorista.

## Migration Plan

- Implantar antes das 08:00 do dia em que o texto novo deve valer.
- Se for preciso voltar, o texto antigo e a ausência de lembrete retornam com a versão anterior. Nenhum dado financeiro muda.
