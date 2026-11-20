# Spec Delta

## Purpose

Registrar uma escala que não chegou pelo WhatsApp, com data e rotas informadas, e seguir o pedido de paradas do dia.

## ADDED Requirements

### Requirement: Acesso autenticado

**Tipo**: Requisito não funcional

O endpoint de escala manual SHALL aceitar a requisição só quando o segredo configurado do webhook conferir, pelo cabeçalho Authorization Bearer ou apikey. Segredo ausente SHALL responder sem gravar. Credencial inválida MUST NOT alterar o dia nem aparecer na resposta ou no log.

#### Scenario: Credencial inválida

- **GIVEN** o segredo do webhook está configurado
- **WHEN** a requisição chega sem a credencial esperada
- **THEN** nada é gravado
- **AND** nenhuma mensagem é enviada

#### Scenario: Segredo não configurado

- **GIVEN** o segredo do webhook está vazio
- **WHEN** a requisição chega
- **THEN** o endpoint não grava a escala

### Requirement: Corpo da escala

**Tipo**: Requisito funcional

O corpo SHALL trazer uma data e ao menos uma rota. Cada rota SHALL ter código e uma ou mais cidades, na ordem da escala. A rota sem o indicador de compartilhada SHALL ser completa. Sem data válida, sem código ou sem cidade, o sistema MUST NOT gravar.

#### Scenario: Escala da madrugada

- **GIVEN** a data 20/11/2026 e a rota completa D9_PM1 com a cidade Congonhinhas
- **WHEN** o corpo autenticado é aceito
- **THEN** essa data fica com essa rota e essas cidades, nessa ordem
- **AND** a quantidade de paradas permanece ausente

#### Scenario: Corpo incompleto

- **GIVEN** uma rota sem cidade
- **WHEN** a requisição autenticada chega
- **THEN** o dia não é alterado

### Requirement: Sem leitura e sem valor inventado

**Tipo**: Regra de negócio

O endpoint SHALL gravar só o que veio no corpo. MUST NOT chamar leitura de imagem. MUST NOT preencher parada, quilometragem ou valor financeiro ausente.

#### Scenario: Quilometragem ainda não medida

- **GIVEN** uma escala manual aceita, sem quilometragem no corpo
- **WHEN** o dia é gravado
- **THEN** a quilometragem não recebe um número inventado
- **AND** nenhuma imagem é interpretada

### Requirement: Pedido de paradas após o registro

**Tipo**: Regra de negócio

Se a data gravada é o dia corrente em America/Sao_Paulo e o horário local já passou das 08:00, o sistema SHALL enviar o pedido formal de paradas quando ele ainda não tiver saído para esses códigos. Antes das 08:00, SHALL deixar o pedido para o relógio. MUST NOT enviar mensagem no grupo de origem.

#### Scenario: Registro depois das 08:00

- **GIVEN** a escala de hoje ainda sem pedido de paradas
- **AND** o horário local é 08:10
- **WHEN** o endpoint grava as rotas
- **THEN** o motorista recebe o pedido formal, com os códigos informados
- **AND** o grupo de origem não recebe mensagem

#### Scenario: Registro de madrugada

- **GIVEN** a escala de hoje
- **AND** o horário local é 00:40
- **WHEN** o endpoint grava as rotas
- **THEN** nenhuma mensagem sai nesse momento
- **AND** o pedido fica para as 08:00

#### Scenario: Mesmos códigos já pedidos

- **GIVEN** o pedido formal já saiu para os códigos informados
- **AND** a quantidade de paradas continua ausente
- **WHEN** o mesmo corpo chega outra vez depois das 08:00
- **THEN** o motorista não recebe um segundo pedido

#### Scenario: Códigos corrigidos antes da resposta

- **GIVEN** o pedido já saiu e a quantidade de paradas continua ausente
- **WHEN** um corpo novo traz códigos diferentes
- **THEN** as rotas do dia passam a ser as do corpo novo
- **AND** o motorista recebe um pedido formal com esses códigos

### Requirement: Dia já respondido

**Tipo**: Exceção

Se o dia já tem quantidade de paradas registrada, o endpoint MUST NOT substituir rotas, paradas nem pagamento.

#### Scenario: Paradas já informadas

- **GIVEN** o dia 19/11/2026 com 63 paradas já registradas
- **WHEN** uma nova escala manual dessa data chega
- **THEN** as rotas e as paradas permanecem como estavam
