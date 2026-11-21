# Design

## Context

O comando só é lido depois que a mensagem deixa de ser tratada como própria. Veja proposal.md para o caso do número conectado.

## Goals / Non-Goals

**Goals:**

- Responder `/ajuda` na conversa em que ele foi escrito, com os quatro comandos que já executam.
- Aceitar esse comando quando a sessão marca a mensagem como própria e o destino é o grupo de controle.

**Non-Goals:**

- Não implementar cadastro, consulta, fechamento nem reenvio.
- Não responder no grupo de origem.
- Não alterar dia, parada, rota ou valor.

## Decisions

- `/ajuda` é um comando próprio, sem argumento. A resposta cita `/ajustar combustivel`, `/manutencao`, `/pnr` e `/ajuda`, e diz que o valor sai do sistema.
- A resposta vai para o mesmo identificador da conversa autorizada. No grupo de controle, esse identificador é o do grupo.
- Mensagem marcada como própria só segue quando o texto é um comando e a conversa é o grupo de controle ou uma conversa particular já autorizada. No grupo de origem, continua sem efeito.
- O texto da ajuda tem várias linhas, então a própria resposta não casa de novo com `/ajuda`.

Alternativa descartada: listar também fechamento, reenvio e cadastro. Esses comandos ainda não executam, e a ajuda passaria a prometer o que o backend não faz.

## Risks / Trade-offs

- [A resposta da ajuda volta pelo webhook como mensagem própria] → o texto inteiro não é um comando, então não gera outra resposta.

## Migration Plan

- Implantar e escrever `/ajuda` no grupo de controle pelo número conectado.
- A versão anterior simplesmente não responde. Nenhum dado já gravado muda.
