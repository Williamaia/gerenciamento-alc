# Auditoria e histórico

## Purpose

Registrar de forma durável quem alterou cadastro, operação, pagamento e fechamento, e permitir que o agente consulte esse histórico pelo backend.

## Objetivo

A trilha explica o estado atual sem substituí-lo. Correção, reenvio e versão revisada ficam reconstruíveis. O registro de auditoria não é apagado pelo fluxo normal.

## Dependências

- `database-management`: persistência e transação junto da alteração.
- `driver-payments`, `financial-reports`, `driver-management`, `route-management`: fatos auditados.
- `whatsapp-integration`: histórico de mensagens.
- `ai-agent`: consulta oficial do histórico.
- `security-and-permissions`: identifica o ator autorizado.

## Requirements

### Requirement: Trilha de alteração

**Tipo**: Requisito funcional

Toda alteração de cadastro operacional, operação, pagamento, paradas, quilometragem, fechamento e configuração SHALL gerar registro de auditoria com ator, origem, instante em America/Sao_Paulo, identificador do registro e estado anterior e posterior.

#### Scenario: Ajuste feito por administrador

- **GIVEN** um administrador autorizado corrige uma operação
- **WHEN** a correção é confirmada
- **THEN** a auditoria identifica o número administrador, a mensagem de origem e os valores anterior e novo

#### Scenario: Ação do agendamento

- **GIVEN** o fechamento disparado pelo horário
- **WHEN** a consolidação termina
- **THEN** a auditoria atribui a ação ao sistema
- **AND** registra o período e a versão

### Requirement: Imutabilidade

**Tipo**: Regra de negócio

O sistema MUST NOT alterar ou apagar registro de auditoria pelo fluxo de negócio. Correção posterior SHALL acrescentar novo registro, não reescrever o anterior.

#### Scenario: Segunda correção

- **GIVEN** uma operação já corrigida uma vez
- **WHEN** outro ajuste autorizado ocorre
- **THEN** os dois registros de auditoria permanecem
- **AND** o estado atual da operação reflete só o último ajuste

### Requirement: Histórico de correção

**Tipo**: Requisito funcional

O sistema SHALL reconstruir a sequência de correções de uma operação, inclusive quantidade, modalidade, código, paradas, quilometragem e pagamento, com o motivo ou o comando recebido.

#### Scenario: Consulta da correção

- **GIVEN** uma operação que passou de duas rotas completas para uma
- **WHEN** o histórico é consultado
- **THEN** aparecem o estado de duas rotas e o estado posterior de uma rota
- **AND** a data da escala permanece a mesma

### Requirement: Histórico de comunicação

**Tipo**: Requisito funcional

O sistema SHALL conservar o vínculo entre mensagem recebida, interpretação, mensagem enviada, documento e falha de entrega. Reenvio SHALL aparecer como novo envio da mesma versão, não como novo fechamento.

#### Scenario: Reenvio auditado

- **GIVEN** um demonstrativo reenviado
- **WHEN** a auditoria da versão é consultada
- **THEN** constam o envio original e o reenvio
- **AND** continua existindo uma única versão financeira para esses dois envios

### Requirement: Versões de fechamento

**Tipo**: Requisito funcional

O sistema SHALL conservar cada versão consolidada, seu PDF, seu total e o motivo da revisão. A versão substituída SHALL continuar legível e MUST NOT ser somada à versão vigente.

#### Scenario: Consulta depois da revisão

- **GIVEN** um período com versão 1 e versão 2
- **WHEN** o histórico do fechamento é consultado
- **THEN** as duas versões e seus totais estão disponíveis
- **AND** a versão vigente é a 2

### Requirement: Consulta pelo agente

**Tipo**: Regra de negócio

Quando o agente precisar de histórico, SHALL obtê-lo do backend. A resposta SHALL distinguir estado atual de estado antigo. O agente MUST NOT completar lacuna da auditoria com memória do modelo.

#### Scenario: Pergunta sobre correção antiga

- **GIVEN** um administrador pergunta qual era o pagamento antes da correção
- **WHEN** o agente responde
- **THEN** usa o estado anterior registrado na auditoria
- **AND** não apresenta um valor que não esteja nessa trilha

### Requirement: Falha também auditada

**Tipo**: Exceção

Bloqueio de fechamento, recusa de autorização e falha definitiva de envio SHALL gerar registro consultável, sem fingir que a ação foi concluída.

#### Scenario: Fechamento bloqueado

- **GIVEN** um fechamento recusado por pendência
- **WHEN** a auditoria é consultada
- **THEN** constam o bloqueio e as pendências informadas
- **AND** não consta consolidação bem-sucedida dessa tentativa

## Exceções cobertas

- Auditoria não é reescrita nem apagada.
- Reenvio não aparece como novo fechamento.
- Versão antiga não é somada à vigente.
- Bloqueio e recusa não são registrados como sucesso.
- Lacuna de auditoria não é preenchida pelo modelo.
