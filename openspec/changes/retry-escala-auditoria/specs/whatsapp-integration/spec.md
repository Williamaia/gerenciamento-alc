# Spec Delta

## MODIFIED Requirements

### Requirement: Envio somente a destinos autorizados

**Tipo**: Regra de negócio

O sistema SHALL enviar texto e PDF apenas ao grupo de controle, ao grupo de auditoria, a um administrador cadastrado ou ao telefone cadastrado de um motorista quando o backend solicitar o envio. O grupo de auditoria SHALL receber texto de sucesso e de falha operacional. O título SHALL começar com ✅ no sucesso e com ❌ na falha. O sistema MUST NOT iniciar conversa com contato ou grupo fora dessa lista.

#### Scenario: Resumo no grupo de controle

- **GIVEN** um pedido do backend para publicar um resumo já persistido
- **WHEN** o envio é executado
- **THEN** o texto sai somente para o grupo de controle cadastrado
- **AND** o identificador da mensagem enviada fica registrado

#### Scenario: Conversa particular desconhecida

- **GIVEN** uma mensagem particular de um número que não é administrador nem motorista cadastrado
- **WHEN** o evento é recebido
- **THEN** o sistema não responde
- **AND** não envia mensagem espontânea a esse número

#### Scenario: Falha no grupo de auditoria

- **GIVEN** uma falha ao ler a escala
- **WHEN** o aviso é enviado
- **THEN** o texto sai somente para o grupo de auditoria cadastrado
- **AND** o título começa com ❌
- **AND** o texto diz o que houve e um único próximo passo
- **AND** o grupo de controle não recebe esse aviso
- **AND** o grupo de origem não recebe mensagem

#### Scenario: Foto lida no grupo de auditoria

- **GIVEN** uma escala lida com confiança e gravada
- **WHEN** o aviso é enviado
- **THEN** o grupo de auditoria recebe o texto de que a foto foi lida
- **AND** o título começa com ✅
- **AND** o grupo de controle não recebe esse aviso
- **AND** o grupo de origem não recebe mensagem

### Requirement: Destinos parametrizáveis

**Tipo**: Regra de negócio

O sistema SHALL obter grupo de origem, grupo de controle, grupo de auditoria, números de administrador e telefones de motorista da configuração persistida. Esses valores MUST NOT estar escritos como condição fixa no código.

#### Scenario: Troca do grupo de controle

- **GIVEN** um administrador altera o grupo de controle na configuração
- **WHEN** o próximo resumo é publicado
- **THEN** o envio usa o novo grupo
- **AND** o grupo anterior deixa de receber mensagens do sistema

#### Scenario: Troca do grupo de auditoria

- **GIVEN** um administrador altera o grupo de auditoria na configuração
- **WHEN** o próximo aviso de sucesso ou falha é enviado
- **THEN** o envio usa o novo grupo
- **AND** o grupo anterior deixa de receber o aviso

#### Scenario: Auditoria sem configuração

- **GIVEN** nenhuma identificação de grupo de auditoria na configuração
- **WHEN** uma falha operacional ocorre
- **THEN** o aviso não é enviado ao grupo de controle
- **AND** a falha permanece só no log do processo
