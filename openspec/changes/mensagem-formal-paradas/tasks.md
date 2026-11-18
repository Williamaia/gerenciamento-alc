# Tasks

## 1. Texto do pedido

- [x] 1.1 Trocar o pedido das 08:00 pelo texto formal, com os códigos em linhas separadas, e verificar no teste que a mensagem contém a saudação, o pedido, os códigos e o aviso de que a resposta é só a quantidade de paradas.
- [x] 1.2 Acrescentar o texto do lembrete e verificar no teste que ele pede de novo as mesmas rotas e mantém o aviso sobre pacotes.

## 2. Lembrete das 10:00

- [x] 2.1 Enviar o lembrete uma vez a partir das 10:00 do mesmo dia quando o pedido já saiu e a quantidade continua ausente, e verificar no teste que o motorista recebe só essa mensagem extra.
- [x] 2.2 Não enviar lembrete quando a quantidade já foi informada, não enviar de novo depois do primeiro lembrete e não responder outra fala do motorista. Verificar esses três casos no teste.
- [x] 2.3 Não cobrar o dia anterior quando o relógio já virou, e verificar no teste que nenhuma mensagem sai para essa data.

## 3. Conferência

- [x] 3.1 Rodar a suíte de testes e confirmar que o pedido, o lembrete e o parecer no grupo de controle continuam separados.
