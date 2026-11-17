# Cálculo de quilometragem

## Purpose

Calcular a quilometragem oficial pela soma dos trechos entre trevos, da saída do barracão ao retorno, usando somente distâncias cadastradas e deixando o resultado pendente quando faltar trecho.

## Objetivo

A conta é trevo a trevo. Centro urbano, mapa externo e estimativa não completam lacuna. O total do dia só fica oficial quando cada rota considerada também tem total oficial. Ajuste manual do administrador fica distinguível do cálculo.

## Dependências

- `route-management`: sequência, cidades e trevos.
- `vehicle-management`: ponto de saída do barracão.
- `driver-payments`: a quilometragem não altera o pagamento do motorista.
- `financial-reports`: exibe o total oficial ou a pendência.
- `whatsapp-commands`: ajuste manual de quilometragem.
- `database-management`: distâncias e precisão decimal.

## Requirements

### Requirement: Fórmula trevo a trevo

**Tipo**: Regra de negócio

O sistema SHALL calcular a rota como ida do barracão ao trevo da primeira cidade, mais os trechos entre os trevos na sequência, mais o retorno do último trevo ao barracão. MUST NOT usar distância entre centros urbanos.

#### Scenario: Soma dos trechos cadastrados

- **GIVEN** distâncias cadastradas de 10,00 km do barracão ao primeiro trevo, 4,50 km até o trevo seguinte e 11,00 km de retorno ao barracão
- **WHEN** a quilometragem dessa rota é calculada
- **THEN** o total oficial é 25,50 km
- **AND** nenhum outro trecho entra na soma

#### Scenario: Sequência com três cidades

- **GIVEN** trechos oficiais de ida 8,00 km, primeiro intervalo 3,00 km, segundo intervalo 2,00 km e retorno 9,00 km
- **WHEN** a rota é calculada
- **THEN** o total oficial é 22,00 km

### Requirement: Distância cadastrada e reutilizável

**Tipo**: Requisito funcional

O sistema SHALL guardar cada distância entre dois trevos, com sentido, e reutilizá-la nas operações seguintes. O cadastro SHALL ser manual. O sistema MUST NOT preencher distância ausente com serviço externo, simetria ou estimativa.

#### Scenario: Trecho reutilizado

- **GIVEN** uma distância já cadastrada entre dois trevos
- **WHEN** outra operação usa o mesmo sentido
- **THEN** o cálculo usa o valor cadastrado
- **AND** não pede nova medição

#### Scenario: Sentido inverso ausente

- **GIVEN** a distância do trevo A ao trevo B cadastrada
- **AND** a distância do trevo B ao trevo A não cadastrada
- **WHEN** o percurso precisa do sentido de B para A
- **THEN** esse trecho fica pendente
- **AND** o valor de A para B não é copiado

### Requirement: Zero não é ausência

**Tipo**: Regra de negócio

Distância cadastrada como zero SHALL ser um trecho válido de zero quilômetro. Distância inexistente MUST NOT ser tratada como zero.

#### Scenario: Trecho explicitamente zerado

- **GIVEN** dois trevos consecutivos com distância cadastrada de 0,00 km e os demais trechos cadastrados
- **WHEN** a rota é calculada
- **THEN** o trecho contribui com zero
- **AND** o total oficial inclui os demais trechos

#### Scenario: Trecho sem cadastro

- **GIVEN** um trecho obrigatório sem distância
- **WHEN** a rota é calculada
- **THEN** não existe total oficial
- **AND** o sistema não grava zero nesse trecho

### Requirement: Pendência sem total parcial

**Tipo**: Exceção

Se faltar barracão, trevo, sequência ou qualquer trecho, o sistema SHALL marcar a quilometragem como pendente e identificar o que falta. MUST NOT publicar a soma dos trechos restantes como total oficial.

#### Scenario: Retorno ausente

- **GIVEN** ida e intervalos cadastrados e retorno sem distância
- **WHEN** o resultado é consultado
- **THEN** a quilometragem fica pendente
- **AND** a soma da ida com os intervalos não é apresentada como total da rota

### Requirement: Total do dia

**Tipo**: Regra de negócio

O sistema SHALL somar os totais oficiais das rotas do veículo na data. Se qualquer rota considerada estiver pendente, o total do dia SHALL ficar pendente.

#### Scenario: Duas rotas oficiais

- **GIVEN** duas rotas do mesmo veículo e data com totais oficiais de 25,50 km e 10,00 km
- **WHEN** o total do dia é calculado
- **THEN** o resultado oficial é 35,50 km

#### Scenario: Uma rota pendente

- **GIVEN** uma rota com total oficial e outra pendente no mesmo dia e veículo
- **WHEN** o resumo do dia é produzido
- **THEN** a quilometragem do dia fica pendente

### Requirement: Ajuste manual

**Tipo**: Exceção

Um administrador autorizado SHALL poder informar a quilometragem do dia. O valor SHALL ser guardado como informado manualmente, sem alterar a tabela de distâncias. Enquanto vigorar, o resumo SHALL usar esse valor e a auditoria SHALL conservar a origem.

#### Scenario: Quilometragem informada

- **GIVEN** uma operação com cálculo pendente
- **WHEN** o administrador autorizado informa 180 km
- **THEN** o valor do dia passa a 180 km com origem manual
- **AND** as distâncias cadastradas permanecem iguais
- **AND** o pagamento do motorista não muda por causa desse número

### Requirement: Precisão

**Tipo**: Requisito não funcional

O sistema SHALL somar quilômetros com tipo decimal e duas casas no resultado exibido. A soma SHALL ser exatamente a soma dos trechos cadastrados, sem arredondamento binário de ponto flutuante.

#### Scenario: Soma com centésimos

- **GIVEN** trechos cadastrados de 0,10 km, 0,20 km e 0,30 km
- **WHEN** a rota é calculada
- **THEN** o total oficial é 0,60 km

## Exceções cobertas

- Sentido inverso não é presumido.
- Trecho vazio não vira zero.
- Total parcial não é publicado como oficial.
- Uma rota pendente deixa o dia pendente.
- Ajuste manual não reescreve a tabela nem o pagamento.
