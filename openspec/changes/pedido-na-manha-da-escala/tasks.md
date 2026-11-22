# Tasks

## 1. Horário do pedido

- [x] 1.1 Não enviar mensagem quando a escala chega. Verificar no teste que a de 22/11 recebida às 23:09 de 21/11 e a recebida às 04:30 de 22/11 ficam para as 08:00.
- [x] 1.2 Verificar no teste que, havendo rota dele, o relógio das 08:00 de 22/11 envia o pedido uma vez.

## 2. Rota de outra pessoa

- [x] 2.1 Tratar leitura confiável sem rota como motorista fora da escala, sem aviso de foto ilegível e sem pedido de paradas.
- [x] 2.2 Não manter a B25_PM1 gravada para 22/11 e verificar no teste que nem o pedido nem o lembrete das 10:00 saem.

## 3. Conferência

- [x] 3.1 Rodar a suíte e confirmar que o pedido formal e o lembrete do mesmo dia continuam valendo.
