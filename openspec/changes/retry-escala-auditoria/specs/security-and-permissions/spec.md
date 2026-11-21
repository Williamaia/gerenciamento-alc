# Spec Delta

## MODIFIED Requirements

### Requirement: Grupos e motorista

**Tipo**: Regra de negócio

O sistema SHALL tratar os grupos cadastrados de origem, de controle e de auditoria. O grupo de auditoria SHALL receber sucesso e falha operacionais. O título SHALL começar com ✅ no sucesso e com ❌ na falha. Comando escrito nele MUST NOT alterar dado. O motorista SHALL poder receber o próprio demonstrativo e MUST NOT alterar dado financeiro, mesmo que escreva um comando válido.

#### Scenario: Comando válido de quem não é administrador

- **GIVEN** qualquer remetente não administrador envia "/ajustar douglas rotas=0"
- **WHEN** a autorização é avaliada
- **THEN** o comando não é aplicado
- **AND** nenhuma resposta revela dados financeiros de terceiros

#### Scenario: Comando no grupo de auditoria

- **GIVEN** um comando escrito no grupo de auditoria
- **WHEN** a autorização é avaliada
- **THEN** o comando não é aplicado
- **AND** o grupo de origem não recebe mensagem

### Requirement: Logs

**Tipo**: Requisito não funcional

O sistema SHALL emitir log em cada passo operacional, com evento, resultado e instante. Log MUST NOT incluir segredo, credencial, PDF nem a imagem. Sucesso e falha operacionais SHALL ir ao grupo de auditoria quando ele estiver configurado. O título SHALL começar com ✅ no sucesso e com ❌ na falha. MUST NOT ir ao grupo de controle nem ao de origem. Passo sem efeito MUST NOT gerar aviso.

#### Scenario: Falha de envio

- **GIVEN** uma falha ao enviar mensagem
- **WHEN** a falha é registrada
- **THEN** o log permite identificar a mensagem e o resultado
- **AND** não contém a chave da API
- **AND** o grupo de auditoria recebe a falha sem a chave
- **AND** o título desse aviso começa com ❌
- **AND** o texto diz que o envio falhou
- **AND** diz que o `/retry` não reenvia essa mensagem
- **AND** não aponta o endpoint manual de escala
- **AND** o grupo de controle não recebe essa falha

#### Scenario: Foto lida com sucesso

- **GIVEN** uma escala lida com confiança e gravada
- **WHEN** o passo é concluído
- **THEN** o grupo de auditoria recebe aviso de que a foto foi lida
- **AND** o título começa com ✅
- **AND** o aviso traz a data e os códigos, sem valor e sem a imagem
- **AND** o grupo de controle não recebe esse aviso

#### Scenario: Passo sem efeito

- **GIVEN** a agenda roda e não há nada a gravar nem a enviar
- **WHEN** o ciclo termina
- **THEN** o log do processo registra o ciclo
- **AND** o grupo de auditoria não recebe aviso

## ADDED Requirements

### Requirement: Erro diz o caminho

**Tipo**: Exceção

Todo aviso de falha no grupo de auditoria SHALL dizer o que houve e um único próximo passo. Falha ao baixar a foto ou falha do leitor antes de responder SHALL indicar `/retry` no grupo de controle. Data ausente, data ambígua ou leitura que segue sem confiança depois do `/retry` SHALL indicar o endpoint manual de escala e MUST NOT dizer que o `/retry` resolve. MUST NOT incluir segredo.

#### Scenario: Foto não baixada

- **GIVEN** o arquivo da escala não pôde ser baixado
- **WHEN** o aviso de falha é enviado
- **THEN** ele diz que a foto não foi baixada
- **AND** indica `/retry` no grupo de controle para baixar e ler de novo
- **AND** não pede o endpoint manual

#### Scenario: Leitor não respondeu

- **GIVEN** a foto foi baixada e o leitor falhou antes de responder
- **WHEN** o aviso de falha é enviado
- **THEN** ele diz que a leitura não terminou
- **AND** indica `/retry` para tentar de novo
- **AND** não pede o endpoint manual

#### Scenario: Primeira leitura sem confiança

- **GIVEN** a foto foi baixada e a primeira leitura não é confiável
- **AND** o `/retry` ainda não foi usado nessa imagem
- **WHEN** o aviso de falha é enviado
- **THEN** ele diz que a foto não foi lida com segurança
- **AND** indica `/retry` para baixar e ler do começo
- **AND** não pede o endpoint manual

#### Scenario: Data que a nova tentativa não resolve

- **GIVEN** o texto da mensagem não tem data utilizável, tem mais de uma data ou pede confirmação
- **WHEN** o aviso de falha é enviado
- **THEN** ele diz o que está errado na data
- **AND** diz que o `/retry` não resolve
- **AND** pede o registro da escala no endpoint manual

#### Scenario: Leitura insegura depois do retry

- **GIVEN** o `/retry` já rodou e a leitura continua sem confiança
- **WHEN** o aviso de falha é enviado
- **THEN** ele diz que a foto foi lida de novo sem confiança
- **AND** diz que outro `/retry` não é o caminho
- **AND** pede o registro da escala no endpoint manual

#### Scenario: Dia que já tem paradas

- **GIVEN** o dia da imagem pendente já tem paradas informadas
- **WHEN** o `/retry` é recusado
- **THEN** o aviso diz que esse dia já tem paradas
- **AND** diz que o `/retry` não altera o dia
- **AND** não aponta o endpoint manual como forma de reescrever o dia

### Requirement: Aviso sem modelo

**Tipo**: Regra de negócio

O texto do log e o aviso do grupo de auditoria SHALL ser montado pelo sistema e SHALL sair pela Evolution. MUST NOT chamar o modelo de IA para redigir, resumir ou classificar esse texto. A leitura da foto da escala continua no modelo já usado para isso.

#### Scenario: Sucesso sem modelo

- **GIVEN** uma escala lida com confiança e gravada
- **WHEN** o aviso de sucesso é enviado ao grupo de auditoria
- **THEN** o texto é montado pelo sistema e sai pela Evolution
- **AND** o modelo de IA não é chamado para escrever esse aviso

#### Scenario: Erro sem modelo

- **GIVEN** uma falha ao baixar ou ler a escala
- **WHEN** o aviso de erro é enviado ao grupo de auditoria
- **THEN** o modelo de IA não é chamado para explicar a falha
- **AND** o aviso continua dizendo o que houve e o próximo passo
