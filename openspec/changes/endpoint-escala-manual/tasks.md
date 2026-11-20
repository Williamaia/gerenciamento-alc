# Tasks

## 1. Endpoint autenticado

- [x] 1.1 Publicar `POST /operacoes/escala` com a mesma conferência de segredo do webhook e verificar no teste que credencial ausente ou errada não grava nem envia mensagem.
- [x] 1.2 Recusar corpo sem data válida, sem código ou sem cidade, e verificar no teste que o dia permanece intocado.

## 2. Gravação e pedido

- [x] 2.1 Gravar as rotas informadas, sem leitura de imagem e sem preencher parada ou quilometragem, e verificar no teste que a ordem das cidades permanece e a parada fica ausente.
- [x] 2.2 Depois das 08:00, enviar o pedido formal ao motorista e não enviar nada ao grupo de origem. Antes das 08:00, não enviar. Verificar os dois horários no teste.
- [x] 2.3 Não reenviar o pedido quando os códigos já foram pedidos, substituir as rotas e pedir de novo quando os códigos mudam, e recusar o dia que já tem paradas. Verificar esses três casos no teste.

## 3. Conferência

- [x] 3.1 Rodar a suíte e confirmar que o webhook existente continua aceitando evento autenticado.
