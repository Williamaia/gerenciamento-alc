# Proposal

## Why

Quando a escala não é lida, o aviso de erro cai no grupo Gerenciamento ALC IA, no meio do parecer do dia. O administrador precisa pedir de novo a mesma foto, e o pedido tem de funcionar mesmo quando quem escreve é o número ligado à sessão.

## What Changes

- O comando `/retry`, no grupo de controle, recomeça a escala do início: baixa a foto de novo, lê a imagem com a mesma leitura, resolve a data e grava o que for confiável. A leitura anterior não é reaproveitada.
- O aviso de falha deixa o grupo de controle e passa para o grupo de auditoria configurado, de nome Audit ALC IA.
- O mesmo grupo recebe o sucesso operacional. A foto lida e gravada gera aviso de sucesso. O título começa com ✅ no sucesso e com ❌ na falha.
- O aviso de erro diz o que houve e um único próximo passo: `/retry` no grupo de controle, ou o endpoint manual de escala quando a mesma foto não resolve.
- Cada passo operacional passa a deixar log. Sucesso e falha vão ao grupo de auditoria, sem segredo e sem a imagem. Passo sem efeito fica só no processo.
- O texto desse aviso é montado pelo sistema e enviado pela Evolution. O modelo de IA não redige log nem aviso.
- Sem grupo de auditoria configurado, a falha fica só no log do processo. O grupo de controle e o de origem não recebem esse erro.

## Capabilities

### New Capabilities

- Nenhuma.

### Modified Capabilities

- `whatsapp-commands`: o comando `/retry` recomeça o caminho completo da última escala não gravada.
- `image-processing`: a leitura que falha guarda a mensagem para uma nova tentativa, sem gravar palpite.
- `whatsapp-integration`: o grupo de auditoria entra nos destinos autorizados para sucesso e falha, e o identificador vem da configuração.
- `security-and-permissions`: o log cobre cada passo operacional, e sucesso e falha vão ao grupo de auditoria com emoticon no título. O erro diz a causa e se o próximo passo é `/retry` ou o endpoint manual. O texto sai pela Evolution, sem o modelo de IA.

## Impact

- Comando, leitura da escala, envio e o log do processo.
- Nova configuração do grupo de auditoria. O parecer, o pedido de paradas e a quinzena continuam nos destinos de hoje.
