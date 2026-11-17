# Agendamento de tarefas

## Purpose

Disparar os dois fechamentos mensais às 17:00 no fuso America/Sao_Paulo, recuperar execução perdida após queda e impedir que duas execuções consolidem o mesmo período ao mesmo tempo.

## Objetivo

O agendamento é persistente e apenas inicia o fechamento definido nos relatórios financeiros. Comando manual usa o mesmo fluxo. Reinício não cancela um fechamento ainda não concluído nem cria outro lançamento.

## Dependências

- `financial-reports`: regra de consolidação, bloqueio, PDF e versão.
- `database-management`: estado persistido do agendamento e da trava.
- `whatsapp-commands`: comando manual de fechamento.
- `security-and-permissions`: ator do disparo manual.
- `audit-and-history`: registra execução, bloqueio e recuperação.

## Requirements

### Requirement: Dois fechamentos mensais

**Tipo**: Regra de negócio

O sistema SHALL iniciar o primeiro fechamento às 17:00 do dia 15, cobrindo do dia 1 ao dia 15 inclusive, e o segundo às 17:00 do último dia do mês, cobrindo do dia 16 ao último dia inclusive. O horário SHALL seguir America/Sao_Paulo e MUST NOT usar um deslocamento fixo de UTC como substituto.

#### Scenario: Dia 15

- **GIVEN** o relógio local de America/Sao_Paulo chega a 17:00 de um dia 15
- **WHEN** o agendamento dispara
- **THEN** o período solicitado vai do dia 1 ao dia 15 daquele mês
- **AND** o disparo não ocorre às 17:00 de outro fuso

#### Scenario: Mês de 31 dias

- **GIVEN** um mês com 31 dias
- **WHEN** chega 17:00 do dia 31 no fuso America/Sao_Paulo
- **THEN** o período solicitado vai do dia 16 ao dia 31

#### Scenario: Fevereiro

- **GIVEN** um fevereiro cujo último dia é 28 ou 29
- **WHEN** chega 17:00 desse último dia
- **THEN** o período solicitado vai do dia 16 até esse último dia
- **AND** não é adiado para o dia 30 ou 31

### Requirement: Persistência

**Tipo**: Requisito não funcional

O sistema SHALL guardar o estado do agendamento e da execução no PostgreSQL. Reiniciar a VPS MUST NOT apagar execução pendente, concluir execução que não terminou nem impedir o próximo horário.

#### Scenario: Queda antes de concluir

- **GIVEN** um fechamento iniciado e ainda não concluído
- **WHEN** o processo é reiniciado
- **THEN** a execução continua ou é retomada de forma idempotente
- **AND** não surge uma segunda versão só por causa da queda

### Requirement: Recuperação de horário perdido

**Tipo**: Exceção

Se o processo estiver desligado às 17:00 de um dia de fechamento, o sistema SHALL disparar uma única recuperação ao voltar, caso aquela versão ainda não tenha sido consolidada. Se já tiver sido consolidada, MUST NOT consolidar de novo.

#### Scenario: Volta depois das 17:00

- **GIVEN** o processo voltou depois das 17:00 do dia 15
- **AND** o período ainda não foi consolidado
- **WHEN** a recuperação executa
- **THEN** o fechamento de 1 a 15 é iniciado uma vez

#### Scenario: Volta com período já fechado

- **GIVEN** a versão daquele período já está consolidada
- **WHEN** o processo volta depois do horário
- **THEN** nenhuma nova versão é criada

### Requirement: Concorrência

**Tipo**: Requisito não funcional

O sistema SHALL permitir somente uma execução ativa para o mesmo motorista e período. Disparo do relógio e comando manual simultâneos SHALL compartilhar essa trava.

#### Scenario: Dois disparos juntos

- **GIVEN** o horário de fechamento e um comando manual do mesmo período no mesmo momento
- **WHEN** ambos tentam consolidar
- **THEN** apenas uma execução ativa prossegue
- **AND** a outra reutiliza o resultado ou aguarda a mesma versão

### Requirement: Retentativa controlada

**Tipo**: Requisito não funcional

Falha transitória do fechamento SHALL ser repetida com limite. Esgotado o limite, o sistema SHALL registrar a falha e avisar o administrador. Bloqueio por pendência de negócio MUST NOT ser tratado como falha transitória infinita.

#### Scenario: Pendência de negócio

- **GIVEN** um fechamento bloqueado por escala aguardando confirmação
- **WHEN** o agendamento registra o resultado
- **THEN** ele não fica reexecutando sem nova condição
- **AND** o administrador é avisado das pendências

#### Scenario: Falha transitória

- **GIVEN** uma falha técnica recuperável durante a consolidação
- **WHEN** ainda há tentativa disponível
- **THEN** a execução pode ser repetida dentro do limite
- **AND** a repetição continua idempotente

### Requirement: Mesmo fluxo do comando

**Tipo**: Regra de negócio

O comando autorizado de fechar quinzena SHALL usar o mesmo processamento, os mesmos bloqueios e a mesma idempotência do agendamento. O agendamento MUST NOT ignorar pendência que o comando respeitaria.

#### Scenario: Comando e relógio

- **GIVEN** uma pendência que bloqueia o fechamento
- **WHEN** o horário ou o comando disparam
- **THEN** os dois resultados são bloqueio
- **AND** nenhum dos dois envia PDF final

### Requirement: Um disparo por período

**Tipo**: Regra de negócio

Cada período e motorista SHALL ter um único disparo automático bem-sucedido por versão. O sistema MUST NOT agendar fechamento diário nem criar fechamento em dia que não seja o dia 15 ou o último dia do mês, salvo comando manual explícito.

#### Scenario: Dia comum

- **GIVEN** um dia que não é 15 nem o último do mês
- **WHEN** o relógio chega às 17:00
- **THEN** nenhum fechamento automático começa

### Requirement: Observabilidade

**Tipo**: Requisito não funcional

O sistema SHALL manter estado operacional consultável com processo ativo, acesso ao PostgreSQL, conexão com a Evolution API, profundidade das filas e resultado da última tentativa de fechamento. Dependência que permaneça indisponível SHALL gerar aviso ao administrador. Esse estado MUST NOT incluir segredo.

#### Scenario: Banco indisponível

- **GIVEN** o PostgreSQL fica inacessível
- **WHEN** a verificação operacional executa
- **THEN** o estado registra a falha de banco
- **AND** o administrador é avisado
- **AND** nenhum segredo aparece nesse estado

#### Scenario: Fila parada após reinício

- **GIVEN** imagens ou envios pendentes depois que o processo volta
- **WHEN** o estado operacional é consultado
- **THEN** a profundidade da fila pendente fica visível
- **AND** os itens não são descartados para o estado parecer saudável

## Exceções cobertas

- Queda no horário gera no máximo uma recuperação se ainda não houve consolidação.
- Período já consolidado não é recriado na volta.
- Disparo duplo não cria duas versões.
- Pendência de negócio não entra em retentativa infinita.
- Dia comum não fecha quinzena automaticamente.
- Dependência indisponível não é escondida e não é compensada com descarte de fila.
