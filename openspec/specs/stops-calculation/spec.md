# Cálculo de paradas

## Purpose

Calcular a remuneração progressiva das paradas como indicador financeiro da operação, separado da quantidade e do pagamento do motorista.

## Objetivo

A tarifa muda por faixa e as faixas se acumulam. O indicador não entra no pagamento do motorista, no demonstrativo nem no faturamento da empresa. Quantidade desconhecida permanece vazia.

## Dependências

- `image-processing`: quantidade lida ou ausência de quantidade.
- `whatsapp-commands`: ajuste autorizado da quantidade.
- `driver-payments`: proibição de somar este indicador ao pagamento.
- `financial-reports`: exibição separada no resumo e exclusão do PDF.
- `database-management`: decimal e armazenamento separado.

## Requirements

### Requirement: Faixas progressivas

**Tipo**: Regra de negócio

O sistema SHALL calcular, em reais com duas casas e arredondamento half-up, R$ 0,35 da 1ª à 60ª parada inclusive, R$ 1,90 da 61ª à 90ª inclusive e R$ 0,90 da 91ª em diante. O cálculo SHALL ser acumulativo. MUST NOT aplicar uma única tarifa a todas as paradas.

#### Scenario: Noventa e cinco paradas

- **GIVEN** a quantidade confirmada de 95 paradas
- **WHEN** o indicador é calculado
- **THEN** a 1ª faixa contribui R$ 21,00
- **AND** a 2ª faixa contribui R$ 57,00
- **AND** a 3ª faixa contribui R$ 4,50
- **AND** o indicador total é R$ 82,50

#### Scenario: Limite de sessenta

- **GIVEN** a quantidade confirmada de 60 paradas
- **WHEN** o indicador é calculado
- **THEN** o resultado é R$ 21,00
- **AND** a faixa de R$ 1,90 não é usada

#### Scenario: Sessenta e uma paradas

- **GIVEN** a quantidade confirmada de 61 paradas
- **WHEN** o indicador é calculado
- **THEN** o resultado é R$ 22,90

#### Scenario: Noventa paradas

- **GIVEN** a quantidade confirmada de 90 paradas
- **WHEN** o indicador é calculado
- **THEN** o resultado é R$ 78,00

#### Scenario: Noventa e uma paradas

- **GIVEN** a quantidade confirmada de 91 paradas
- **WHEN** o indicador é calculado
- **THEN** o resultado é R$ 78,90

#### Scenario: Uma parada

- **GIVEN** a quantidade confirmada de 1 parada
- **WHEN** o indicador é calculado
- **THEN** o resultado é R$ 0,35

### Requirement: Quantidade inválida

**Tipo**: Exceção

O sistema SHALL aceitar somente quantidade inteira maior ou igual a zero. Valor negativo, fracionário ou não numérico MUST NOT produzir indicador.

#### Scenario: Quantidade negativa

- **GIVEN** uma quantidade informada menor que zero
- **WHEN** o cálculo é solicitado
- **THEN** o sistema recusa o valor
- **AND** não grava indicador

#### Scenario: Quantidade fracionária

- **GIVEN** uma quantidade de 10,5 paradas
- **WHEN** o cálculo é solicitado
- **THEN** o sistema recusa o valor
- **AND** não arredonda para 10 nem para 11

### Requirement: Ausência não é zero

**Tipo**: Exceção

Quantidade desconhecida SHALL permanecer vazia e o indicador SHALL ficar pendente. Zero SHALL ser usado apenas quando a quantidade zero tiver sido lida ou informada por administrador autorizado.

#### Scenario: Escala sem paradas

- **GIVEN** uma operação confirmada sem quantidade de paradas
- **WHEN** o resumo é montado
- **THEN** as paradas e o indicador ficam pendentes
- **AND** o pagamento do motorista não é zerado por isso

#### Scenario: Zero informado

- **GIVEN** um administrador autorizado informa zero paradas
- **WHEN** o indicador é calculado
- **THEN** a quantidade armazenada é 0
- **AND** o indicador é R$ 0,00

### Requirement: Separação do pagamento

**Tipo**: Regra de negócio

O sistema SHALL armazenar a quantidade de paradas e o indicador em campos separados do pagamento do motorista. O indicador MUST NOT ser somado ao pagamento, ao demonstrativo do motorista ou ao faturamento da operação.

#### Scenario: Dia com rotas e paradas

- **GIVEN** pagamento confirmado de R$ 200,00 e indicador de R$ 82,50
- **WHEN** os totais do dia são consultados
- **THEN** o pagamento do motorista permanece R$ 200,00
- **AND** o indicador de paradas permanece R$ 82,50
- **AND** não existe total que some 282,50 como valor a pagar ao motorista

### Requirement: Total do dia sem duplicar

**Tipo**: Regra de negócio

O sistema SHALL calcular o indicador uma vez sobre a quantidade total do dia. Se a escala trouxer paradas por rota, SHALL somar as quantidades antes do cálculo. Quantidade por rota e total do dia divergentes SHALL ficar aguardando confirmação.

#### Scenario: Paradas divididas nas rotas

- **GIVEN** duas rotas do dia com 40 e 55 paradas e nenhum total conflitante
- **WHEN** o indicador do dia é calculado
- **THEN** a quantidade usada é 95
- **AND** o indicador é R$ 82,50 calculado uma única vez

#### Scenario: Totais divergentes

- **GIVEN** a soma das rotas difere do total escrito na escala
- **WHEN** a validação ocorre
- **THEN** a quantidade fica aguardando confirmação
- **AND** nenhum dos dois números é escolhido automaticamente

### Requirement: Vigência dos parâmetros

**Tipo**: Regra de negócio

As faixas e os valores iniciais desta spec SHALL ser parâmetros do sistema. Alteração posterior SHALL valer para cálculos ainda não confirmados e MUST NOT reescrever indicador já confirmado ou período já consolidado.

#### Scenario: Mudança de tarifa depois da confirmação

- **GIVEN** um indicador diário já confirmado
- **WHEN** um administrador altera o valor de uma faixa
- **THEN** o indicador já confirmado permanece
- **AND** um dia ainda não confirmado usa a faixa nova quando for confirmado

## Exceções cobertas

- Quantidade negativa ou fracionária não gera indicador.
- Quantidade desconhecida não vira zero.
- Totais divergentes não são resolvidos sozinhos.
- Indicador confirmado não é recalculado por mudança posterior de parâmetro.
