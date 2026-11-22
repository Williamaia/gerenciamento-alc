# Spec Delta

## MODIFIED Requirements

### Requirement: Pedido de paradas ao motorista

**Tipo**: Regra de negócio

O pedido de paradas SHALL sair só na data da escala, em America/Sao_Paulo, desde as 08:00, e só se a leitura achar o nome do motorista. A escala pode chegar na véspera ou até as 05:00 desse dia, e nesses horários MUST NOT gerar mensagem. Sem o nome, MUST NOT enviar pedido nem lembrete. O texto SHALL ser o pedido formal, uma vez. Às 10:00, se a quantidade seguir ausente, SHALL enviar um único lembrete. MUST NOT responder outra mensagem nessa conversa. O parecer SHALL ir ao grupo de controle.

#### Scenario: Pedido formal das 08:00

- **GIVEN** o dia tem as rotas do motorista e a quantidade de paradas ainda está ausente
- **WHEN** chega 08:00 dessa data em America/Sao_Paulo
- **THEN** o motorista recebe uma única mensagem formal pedindo só a quantidade de paradas desses códigos
- **AND** nenhuma outra mensagem é enviada nessa conversa nesse horário

#### Scenario: Escala no próprio dia até as 05:00

- **GIVEN** a escala de 22/11 chega em 22/11 às 04:30
- **AND** a leitura encontra o nome do motorista monitorado
- **WHEN** a escala é gravada
- **THEN** nenhuma mensagem de paradas sai nesse momento
- **AND** o pedido fica para as 08:00 de 22/11

#### Scenario: Escala da noite para o dia seguinte

- **GIVEN** a escala de 22/11 é recebida em 21/11 às 23:09
- **WHEN** a leitura é gravada
- **THEN** nenhuma mensagem de paradas sai nesse momento
- **AND** o pedido fica para as 08:00 de 22/11, se houver rota dele nesse dia

#### Scenario: Motorista fora da escala

- **GIVEN** a leitura da escala de 22/11 não encontra o nome Douglas
- **AND** B25_PM1 é rota de outra pessoa
- **WHEN** a leitura termina
- **THEN** nenhuma mensagem é enviada a ele
- **AND** o pedido das 08:00 e o lembrete das 10:00 não saem

#### Scenario: Douglas informa as paradas

- **GIVEN** o pedido das 08:00 já enviado
- **WHEN** ele responde a quantidade de paradas
- **THEN** essa quantidade fica registrada
- **AND** o agente não envia resposta de volta
- **AND** o parecer segue para o grupo de controle

#### Scenario: Lembrete às 10:00

- **GIVEN** o pedido das 08:00 já foi enviado para rota do motorista
- **AND** a quantidade de paradas continua ausente
- **WHEN** chega 10:00 do mesmo dia em America/Sao_Paulo
- **THEN** o motorista recebe um único lembrete
- **AND** um segundo lembrete não é enviado

#### Scenario: Outra mensagem do motorista

- **GIVEN** o pedido de paradas já foi feito
- **WHEN** o motorista envia qualquer outra mensagem
- **THEN** o agente não responde

#### Scenario: Dia seguinte sem resposta

- **GIVEN** a quantidade de paradas de ontem continua ausente
- **WHEN** o relógio já está no dia seguinte
- **THEN** o lembrete de ontem não é enviado
