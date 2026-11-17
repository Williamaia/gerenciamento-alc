# Gestão de rotas

## Purpose

Cadastrar rotas, cidades, sequência, trevos e associações com motoristas e veículos, usando códigos como dados e não como constantes do sistema.

## Objetivo

A rota descreve o percurso e as cidades. A execução do dia aponta para a rota quando ela já existe e conserva o código observado quando ainda não existe. Motoristas diferentes podem executar a mesma rota.

## Dependências

- `vehicle-management`: veículo associado à rota.
- `mileage-calculation`: usa sequência e trevos desta spec.
- `image-processing`: entrega código e cidades observados.
- `driver-management`: motoristas que podem executar a rota.
- `database-management`: unicidade do código e histórico.

## Requirements

### Requirement: Cadastro da rota

**Tipo**: Requisito funcional

O sistema SHALL cadastrar e editar código, nome, cidades atendidas, sequência das cidades, trevos de referência, veículo associado e motoristas associados. O código SHALL ser único.

#### Scenario: Nova rota

- **GIVEN** um administrador informa código ainda não usado, nome e cidades em sequência
- **WHEN** a rota é salva
- **THEN** ela fica disponível para as próximas operações
- **AND** o código não precisa existir previamente no código-fonte

#### Scenario: Código repetido

- **GIVEN** uma rota já cadastrada com um código
- **WHEN** outro cadastro tenta usar o mesmo código
- **THEN** o novo cadastro é recusado
- **AND** a rota original permanece

### Requirement: Código não fixo

**Tipo**: Regra de negócio

O sistema MUST NOT depender de uma lista fixa de códigos de rota no código-fonte. Códigos citados em exemplos, como A24_PM1, SHALL ser dados de demonstração ou cadastro, não regra embutida.

#### Scenario: Código novo na escala

- **GIVEN** uma escala com um código que não está em nenhum exemplo do sistema
- **WHEN** a leitura é aceita
- **THEN** o código observado é armazenado
- **AND** o processamento não falha só porque o código não estava previsto no programa

### Requirement: Vários motoristas na mesma rota

**Tipo**: Regra de negócio

O sistema SHALL permitir que a mesma rota seja executada por motoristas diferentes, no mesmo dia ou em dias diferentes, cada um com sua própria operação.

#### Scenario: Dois motoristas monitorados

- **GIVEN** dois motoristas ativos monitorados associados à mesma rota
- **WHEN** cada um executa essa rota na mesma data
- **THEN** existem duas operações, uma para cada motorista
- **AND** o pagamento de um não altera o do outro

### Requirement: Cidade e trevo de acesso

**Tipo**: Requisito funcional

Cada cidade de uma rota SHALL poder apontar para um trevo de acesso. A sequência SHALL definir a ordem do percurso. O sistema MUST NOT substituir o trevo pelo centro urbano.

#### Scenario: Cidade sem trevo

- **GIVEN** uma cidade da rota sem trevo de acesso cadastrado
- **WHEN** a quilometragem dessa rota é solicitada
- **THEN** a rota permanece cadastrada
- **AND** o cálculo de quilometragem fica pendente

### Requirement: Edição sem apagar execução

**Tipo**: Regra de negócio

Editar cadastro de rota SHALL afetar usos futuros e MUST NOT reescrever silenciosamente execuções já confirmadas. O histórico SHALL conservar o código, as cidades e a sequência usados na execução.

#### Scenario: Sequência alterada depois do dia

- **GIVEN** uma execução já confirmada com uma sequência de cidades
- **WHEN** um administrador altera a sequência cadastrada
- **THEN** a execução antiga conserva a sequência com que foi confirmada
- **AND** a nova sequência vale para execução posterior

### Requirement: Divergência com a escala

**Tipo**: Exceção

Se o código existir e as cidades lidas divergirem do cadastro, o sistema SHALL guardar as cidades observadas, marcar a divergência e MUST NOT alterar o cadastro nem confirmar a quilometragem automaticamente.

#### Scenario: Cidade extra na imagem

- **GIVEN** uma rota cadastrada e uma escala confiável do mesmo código com cidade diferente
- **WHEN** a interpretação é validada
- **THEN** a operação fica com divergência de cidades
- **AND** o cadastro da rota não é sobrescrito pela imagem
- **AND** a quilometragem não é confirmada só com o cadastro ignorando a imagem

### Requirement: Rota ainda não cadastrada

**Tipo**: Exceção

Código observado sem cadastro SHALL ser guardado na execução. Isso MUST NOT, por si só, impedir o pagamento do motorista quando a contagem da rota estiver confirmada. A quilometragem SHALL ficar pendente até haver cadastro e distâncias suficientes.

#### Scenario: Código desconhecido com motorista confirmado

- **GIVEN** uma leitura confiável de uma rota completa de motorista monitorado
- **AND** o código ainda não está cadastrado
- **WHEN** o backend confirma a presença do motorista
- **THEN** o pagamento dessa rota pode ser confirmado pela modalidade
- **AND** a quilometragem permanece pendente
- **AND** o código não é substituído por outro

## Exceções cobertas

- Código duplicado é recusado.
- Cidade sem trevo deixa quilometragem pendente.
- Divergência entre imagem e cadastro não reescreve a rota.
- Código novo não bloqueia o pagamento já confirmado pela modalidade e não inventa distância.
