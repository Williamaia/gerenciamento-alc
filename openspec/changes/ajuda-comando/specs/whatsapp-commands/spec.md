# Spec Delta

## MODIFIED Requirements

### Requirement: Cadastro e ajuda

**Tipo**: Requisito funcional

O comando de cadastrar motorista SHALL conduzir o administrador pelos campos obrigatórios e SHALL exigir os dois valores de rota antes de ativar. O comando /ajuda SHALL responder na mesma conversa autorizada e SHALL listar só os comandos que o backend aceita: ajuste de combustível, manutenção, PNR e ajuda. SHALL informar que os valores são calculados pelo sistema. MUST NOT responder no grupo de origem. Comando do número conectado no grupo de controle SHALL ser aceito.

#### Scenario: Cadastro guiado incompleto

- **GIVEN** o comando autorizado "/cadastrar motorista"
- **WHEN** o administrador ainda não informou os valores das modalidades
- **THEN** o motorista não fica ativo
- **AND** o sistema pede os campos que faltam

#### Scenario: Ajuda

- **GIVEN** o comando autorizado "/ajuda" no grupo de controle
- **WHEN** o comando é recebido
- **THEN** a resposta sai nesse grupo e lista ajuste de combustível, manutenção, PNR e ajuda
- **AND** informa que os valores são calculados pelo sistema
- **AND** o grupo de origem não recebe mensagem
- **AND** nenhum valor, parada ou rota é alterado

#### Scenario: Ajuda escrita pelo número conectado

- **GIVEN** o número conectado à sessão escreve "/ajuda" no grupo de controle
- **WHEN** o evento chega marcado como mensagem da própria sessão
- **THEN** a ajuda é enviada no grupo de controle
