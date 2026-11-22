# Design

## Context

O pedido imediato olha só se o relógio já passou das 08:00. A escala de 22/11 chegou às 23:09 de 21/11, então a mensagem saiu na hora. O leitor devolveu B25_PM1 mesmo sem o motorista nessa rota. Veja proposal.md.

## Goals / Non-Goals

**Goals:**

- Segurar o pedido até as 08:00 da data da escala, venha a foto na véspera ou até as 05:00 do próprio dia.
- Não gravar nem chamar o motorista quando a leitura não achar o nome dele.
- Impedir que o lembrete das 10:00 saia para a B25_PM1 já gravada.

**Non-Goals:**

- Não mudar o texto formal do pedido nem o lembrete.
- Não pedir parada de um dia que já passou.
- Não usar o modelo para redigir o aviso.

## Decisions

- A foto não dispara o pedido. A escala de um dia chega na véspera ou até as 05:00 desse dia. O relógio das 08:00 dessa data é quem envia, e só se a leitura achou o nome.
- Leitura sem o nome Douglas significa que ele não está escalado. A lista de rotas fica vazia. Não é falha, não pede `/retry` e não manda mensagem para ele.
- O leitor só devolve rota quando o nome está na célula do motorista. Código de outra pessoa, como B25_PM1 nesta escala, volta em lista vazia.
- A B25_PM1 gravada para 22/11 é removida, e o pedido já marcado não produz lembrete. Sem rota, o relógio não chama o motorista.

Alternativa descartada: esperar o relógio e ainda assim perguntar a B25_PM1 às 08:00. Ele não está nessa rota.

## Risks / Trade-offs

- [A mensagem das 23:09 já foi enviada] → o código não apaga mensagem antiga. O que muda é não haver outra às 08:00 nem às 10:00.
- [O leitor atribuir de novo uma rota alheia] → a data futura continua sem mensagem à noite. A lista vazia é o resultado exigido quando o nome não está na célula.

## Migration Plan

- Implantar antes das 08:00 de 22/11.
- A versão anterior volta a perguntar na hora em que a foto chega depois das 08:00, mesmo que a escala seja do dia seguinte.
