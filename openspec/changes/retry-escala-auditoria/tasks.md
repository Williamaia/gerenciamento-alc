# Tasks

## 1. Foto pendente e auditoria

- [x] 1.1 Guardar o identificador da última escala não lida e verificar no teste que a falha não grava rota nem avisa o grupo de controle.
- [x] 1.2 Enviar a falha ao grupo de auditoria com título ❌ e a foto lida com título ✅. Sem essa configuração, nenhum dos dois vai ao grupo de controle.
- [x] 1.4 Verificar no teste que o erro diz a causa e um único passo: `/retry` quando a foto não baixou, o leitor não respondeu ou a primeira leitura falhou; endpoint manual quando a data não serve ou o `/retry` já falhou; nenhum dos dois quando o dia já tem paradas ou o envio falhou.
- [x] 1.3 Registrar log em recebimento, leitura, comando, envio, quilometragem e agenda, sem chave, segredo ou imagem. Verificar que o ciclo sem efeito não gera aviso.
- [x] 1.5 Verificar no teste que o aviso de sucesso e o de erro saem pela Evolution com texto do sistema, e que o modelo de IA não é chamado para redigir nenhum dos dois.

## 2. Comando /retry

- [x] 2.1 Aceitar `/retry` do número conectado no grupo de controle e verificar no teste que o arquivo é baixado de novo, o leitor é chamado com esses bytes e o dia gravado sai dessa nova leitura, não da anterior.
- [x] 2.2 Verificar no teste a confirmação só com data e códigos, a recusa quando o dia já tem paradas, o aviso de que não há foto e a ausência de resposta no grupo de origem.

## 3. Conferência

- [x] 3.1 Rodar a suíte e confirmar que o parecer continua no grupo de controle.
