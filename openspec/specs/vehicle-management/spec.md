# Gestão de veículos

## Purpose

Registrar os veículos da frota, começando pela Fiorino de referência, sem limitar a arquitetura a um único veículo nem escrever a placa ou o apelido no código.

## Objetivo

Toda operação confirmada aponta para um veículo cadastrado. A primeira Fiorino é um registro inicial quando o administrador informar seus dados. Novos veículos podem ser incluídos sem mudança de regra de pagamento do motorista.

## Dependências

- `driver-management`: motorista pode apontar para um veículo.
- `route-management`: rota pode apontar para um veículo.
- `driver-payments`: a operação diária inclui o veículo na chave de negócio.
- `database-management`: persistência do cadastro.

## Requirements

### Requirement: Cadastro de veículos

**Tipo**: Requisito funcional

O sistema SHALL cadastrar e editar mais de um veículo, com identificador, descrição, situação ativo ou inativo e base operacional. Placa ou apelido, quando existirem, SHALL ser dados informados e MUST NOT ser literais obrigatórios no código.

#### Scenario: Inclusão de outro veículo

- **GIVEN** já existe uma Fiorino cadastrada
- **WHEN** um administrador cadastra outro veículo ativo
- **THEN** os dois permanecem utilizáveis
- **AND** nenhuma regra precisa nomear apenas a primeira Fiorino

#### Scenario: Dados da primeira Fiorino ainda não informados

- **GIVEN** nenhum veículo foi configurado
- **WHEN** uma escala é interpretada
- **THEN** a leitura pode ser armazenada
- **AND** a operação não é confirmada enquanto não houver veículo ativo associado

### Requirement: Base operacional

**Tipo**: Regra de negócio

O veículo SHALL ter como base inicial o barracão em Santo Antônio da Platina - PR. O endereço detalhado e o ponto de saída SHALL ser configuráveis. O sistema MUST NOT inventar logradouro ou coordenada.

#### Scenario: Ponto de saída não cadastrado

- **GIVEN** um veículo sem ponto de saída cadastrado
- **WHEN** a quilometragem dessa operação é calculada
- **THEN** o cálculo fica pendente
- **AND** nenhuma distância de saída é presumida

### Requirement: Associação operacional

**Tipo**: Regra de negócio

Uma operação diária SHALL referenciar um veículo. Um motorista e uma rota podem estar associados a um veículo sem impedir que outra combinação seja cadastrada depois.

#### Scenario: Mesmo veículo em rotas diferentes

- **GIVEN** um veículo ativo associado a mais de uma rota
- **WHEN** essas rotas são executadas no mesmo dia pelo motorista monitorado
- **THEN** as execuções referenciam esse veículo
- **AND** continuam sendo uma única operação diária daquele motorista, data e veículo

### Requirement: Veículo inativo

**Tipo**: Exceção

O sistema SHALL impedir nova operação confirmada com veículo inativo e SHALL preservar o histórico já vinculado a ele.

#### Scenario: Veículo desativado

- **GIVEN** um veículo inativo
- **WHEN** uma nova escala tenta usá-lo como veículo da operação
- **THEN** a confirmação fica bloqueada
- **AND** operações antigas desse veículo continuam consultáveis

### Requirement: Escopo financeiro desta versão

**Tipo**: Requisito não funcional

Nesta versão, a remuneração do motorista SHALL continuar vinda do cadastro do motorista. O sistema MUST NOT exigir uma tabela de tarifa por veículo para confirmar pagamento. A associação do veículo SHALL permanecer disponível para regra futura.

#### Scenario: Confirmação sem tarifa de veículo

- **GIVEN** motorista com tarifas cadastradas e veículo ativo sem tarifa própria
- **WHEN** a escala dele é confirmada
- **THEN** o pagamento usa as tarifas do motorista
- **AND** a operação guarda o veículo utilizado

## Exceções cobertas

- Sem veículo ativo, a operação não é confirmada.
- Ponto de saída ausente não gera distância.
- Veículo inativo não entra em operação nova.
- Placa desconhecida não é inventada.
