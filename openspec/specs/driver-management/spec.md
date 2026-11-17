# Gestão de motoristas

## Purpose

Cadastrar motoristas, variações de nome, contato, veículo e valores de rota completa e compartilhada, de forma que a regra de pagamento não dependa de um nome escrito no código.

## Objetivo

O cadastro é a origem dos nomes reconhecidos e das tarifas do motorista. Douglas é o primeiro registro de dados, com valores iniciais editáveis. A identificação usa o cadastro, inclusive grafias diferentes.

## Dependências

- `vehicle-management`: veículo associado.
- `driver-payments`: usa as tarifas e o estado do motorista.
- `image-processing`: fornece o nome lido para casamento.
- `security-and-permissions`: só administrador altera cadastro.
- `database-management` e `audit-and-history`: persistência e trilha.

## Requirements

### Requirement: Cadastro do motorista

**Tipo**: Requisito funcional

O sistema SHALL cadastrar e editar motorista com nome oficial, nome alternativo, variações de escrita, identificadores de leitura, telefone, situação ativo ou inativo, veículo associado, valor da rota completa e valor da rota compartilhada.

#### Scenario: Cadastro mínimo válido

- **GIVEN** um administrador informa nome oficial, valores das duas modalidades e situação ativa
- **WHEN** o cadastro é gravado
- **THEN** o motorista passa a ser reconhecível pelas variações informadas
- **AND** os valores ficam disponíveis para operações confirmadas depois da gravação

#### Scenario: Campo obrigatório ausente

- **GIVEN** um cadastro sem valor de rota completa ou sem valor de rota compartilhada
- **WHEN** o administrador tenta salvar
- **THEN** o cadastro não é ativado
- **AND** o sistema informa qual campo falta

### Requirement: Semente inicial do Douglas

**Tipo**: Regra de negócio

Na carga inicial, o sistema SHALL criar, se ainda não existir, o motorista de nome oficial Douglas, ativo, com rota completa de R$ 100,00 e rota compartilhada de R$ 50,00. Esses valores SHALL permanecer editáveis. O nome Douglas MUST NOT ser condição fixa nas regras.

#### Scenario: Primeira carga

- **GIVEN** um banco sem motoristas
- **WHEN** a carga inicial é executada
- **THEN** existe um motorista Douglas ativo com as duas tarifas iniciais
- **AND** ele é o único motorista monitorado para pagamento nessa carga

#### Scenario: Tarifa alterada

- **GIVEN** o motorista Douglas já cadastrado
- **WHEN** um administrador muda a rota completa para outro valor
- **THEN** o novo valor passa a valer para confirmações posteriores
- **AND** operações já confirmadas conservam o valor que já tinham recebido

### Requirement: Reconhecimento de grafia

**Tipo**: Regra de negócio

O sistema SHALL comparar o nome lido com nome oficial, nome alternativo, variações e identificadores, sem diferenciar maiúsculas e acentos. Um único motorista ativo casado SHALL ser o resultado. Mais de um casamento SHALL gerar dúvida.

#### Scenario: Grafia diferente

- **GIVEN** o motorista possui variação cadastrada para o nome lido na escala
- **WHEN** a leitura confiável traz essa grafia
- **THEN** a linha é associada a esse motorista
- **AND** a associação não depende de o nome oficial aparecer idêntico na imagem

#### Scenario: Dois cadastros compatíveis

- **GIVEN** dois motoristas ativos compatíveis com o mesmo texto lido
- **WHEN** o nome é comparado
- **THEN** a linha fica aguardando confirmação
- **AND** nenhum dos dois recebe pagamento automático dessa linha

### Requirement: Motorista inativo

**Tipo**: Exceção

O sistema SHALL impedir nova operação pagável para motorista inativo e SHALL conservar o histórico já gravado. Uma escala que traga somente esse motorista SHALL avisar o administrador.

#### Scenario: Escala de motorista inativo

- **GIVEN** um motorista inativo reconhecido na escala
- **WHEN** a interpretação é validada
- **THEN** nenhuma nova operação pagável é criada para ele
- **AND** os registros antigos continuam consultáveis

### Requirement: Monitoramento de pagamento

**Tipo**: Regra de negócio

O sistema SHALL gerar pagamento apenas para motorista ativo marcado para monitoramento. Nome lido que não case com motorista monitorado SHALL permanecer na leitura da escala, sem pagamento.

#### Scenario: Outra pessoa na escala

- **GIVEN** uma escala confiável com o motorista monitorado e outra pessoa não cadastrada
- **WHEN** a operação é validada
- **THEN** só o motorista monitorado fica elegível a pagamento
- **AND** o nome da outra pessoa permanece registrado na leitura

### Requirement: Telefone e veículo

**Tipo**: Requisito funcional

Telefone e veículo SHALL ser dados do cadastro, nunca literais de código. Ausência de telefone MUST NOT impedir o registro operacional, mas MUST impedir o envio do demonstrativo, conforme a integração.

#### Scenario: Motorista sem telefone

- **GIVEN** um motorista ativo sem telefone
- **WHEN** uma operação dele é confirmada
- **THEN** a operação pode ser gravada
- **AND** o demonstrativo futuro não é tratado como enviado

## Exceções cobertas

- Cadastro incompleto não é ativado.
- Alias ambíguo não escolhe motorista sozinho.
- Motorista inativo não recebe nova operação pagável.
- Pessoa não cadastrada não recebe pagamento.
- Telefone vazio não é preenchido com número inventado.
