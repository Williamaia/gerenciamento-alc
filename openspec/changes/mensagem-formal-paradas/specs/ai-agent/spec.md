# Spec Delta

## MODIFIED Requirements

### Requirement: Pedido de paradas ao motorista

**Tipo**: Regra de negócio

Às 08:00 em America/Sao_Paulo, o agente SHALL enviar ao motorista uma mensagem formal em primeira pessoa, com o código de cada rota, pedindo só a quantidade de paradas. SHALL identificar-se como agente da Frota Plus. SHALL guardar a quantidade respondida. Às 10:00, se a quantidade seguir ausente, SHALL enviar um único lembrete. MUST NOT enviar outra mensagem nessa conversa. O parecer do dia SHALL ir ao grupo de controle. O demonstrativo da quinzena continua no dia 15 e no último dia.

#### Scenario: Pedido formal das 08:00

- **GIVEN** o dia tem as rotas C25_PM1 e C21_PM1 e a quantidade de paradas ainda está ausente
- **WHEN** chega 08:00 em America/Sao_Paulo
- **THEN** o motorista recebe uma única mensagem com o texto "Olá. Sou o agente da Frota Plus.", a frase "Por favor, informe a quantidade de paradas das seguintes rotas:", os códigos C25_PM1 e C21_PM1 em linhas separadas e as frases "Informe somente a quantidade de paradas." e "Não é necessário informar a quantidade de pacotes."
- **AND** nenhuma outra mensagem é enviada nessa conversa nesse horário

#### Scenario: Douglas informa as paradas

- **GIVEN** o pedido das 08:00 já enviado a Douglas
- **WHEN** ele responde a quantidade de paradas
- **THEN** essa quantidade fica registrada
- **AND** o agente não envia resposta de volta
- **AND** o parecer segue para o grupo de controle

#### Scenario: Lembrete às 10:00

- **GIVEN** o pedido das 08:00 já foi enviado
- **AND** a quantidade de paradas continua ausente
- **WHEN** chega 10:00 do mesmo dia em America/Sao_Paulo
- **THEN** o motorista recebe um único lembrete com o texto "Olá. Sou o agente da Frota Plus.", a frase "Ainda não recebi a quantidade de paradas das seguintes rotas:", os códigos das rotas do dia e as frases "Informe somente a quantidade de paradas." e "Não é necessário informar a quantidade de pacotes."
- **AND** um segundo lembrete não é enviado

#### Scenario: Resposta antes do lembrete

- **GIVEN** Douglas já informou a quantidade de paradas antes das 10:00
- **WHEN** chega 10:00 do mesmo dia
- **THEN** o lembrete não é enviado

#### Scenario: Outra mensagem do motorista

- **GIVEN** o pedido de paradas ou o lembrete já foi feito
- **WHEN** Douglas envia qualquer outra mensagem
- **THEN** o agente não responde

#### Scenario: Dia seguinte sem resposta

- **GIVEN** a quantidade de paradas de ontem continua ausente
- **WHEN** o relógio já está no dia seguinte
- **THEN** o lembrete de ontem não é enviado
