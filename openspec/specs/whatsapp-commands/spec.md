# Comandos de WhatsApp

## Purpose

Oferecer ao administrador, pelo WhatsApp, comandos e frases em português para consultar, corrigir, cadastrar motorista, fechar quinzena e reenviar PDF, sempre delegando a decisão ao backend.

## Objetivo

O comando estruturado executa quando o alvo é único. A frase natural percorre a mesma autorização e as mesmas regras. Ação ambígua espera confirmação. Nenhum comando nasce valor financeiro fora do motor de regras.

## Dependências

- `ai-agent`: interpretação da frase e da confirmação.
- `security-and-permissions`: remetente e canal autorizados.
- `driver-payments`: ajustes de rotas.
- `stops-calculation` e `mileage-calculation`: ajustes de paradas e quilometragem.
- `financial-reports`: consulta, fechamento e reenvio.
- `driver-management`: cadastro guiado.
- `whatsapp-integration`: canal da resposta.

## Requirements

### Requirement: Autorização do comando

**Tipo**: Regra de negócio

O sistema SHALL aceitar comando somente de número administrador cadastrado, em conversa particular com o número conectado ou no grupo de controle. Comando de outro remetente, de grupo não autorizado ou do grupo de origem MUST NOT alterar dado.

#### Scenario: Administrador no grupo de controle

- **GIVEN** um número administrador escreve um comando no grupo de controle
- **WHEN** o comando é validado
- **THEN** ele pode ser executado segundo as regras desse comando

#### Scenario: Motorista envia ajuste

- **GIVEN** o telefone cadastrado do motorista envia um comando de ajuste
- **WHEN** o comando é recebido
- **THEN** nenhuma operação ou valor é alterado
- **AND** o sistema não trata o motorista como administrador

### Requirement: Ajuste de rotas completas

**Tipo**: Requisito funcional

O comando de ajustar rotas SHALL definir a quantidade absoluta de rotas completas do motorista na operação resolvida. Se a quantidade nova for menor e houver mais de um código, o sistema SHALL perguntar quais permanecem antes de gravar.

#### Scenario: Ajuste para uma rota

- **GIVEN** o comando autorizado "/ajustar douglas rotas=1"
- **AND** uma única operação resolvida, com uma única rota
- **WHEN** o comando é executado
- **THEN** a operação fica com uma rota completa
- **AND** o valor é recalculado pelo backend

#### Scenario: Quantidade zero sem compartilhada

- **GIVEN** o comando autorizado "/ajustar douglas rotas=0"
- **AND** a operação resolvida não tem rota compartilhada
- **WHEN** o comando é executado
- **THEN** a operação fica não escalada
- **AND** o pagamento passa a R$ 0,00
- **AND** o histórico conserva o estado anterior

#### Scenario: Quantidade zero com compartilhada

- **GIVEN** uma rota completa e uma compartilhada na mesma operação
- **WHEN** o administrador autorizado zera somente as rotas completas
- **THEN** a rota compartilhada permanece
- **AND** o total passa a ser apenas o da compartilhada

#### Scenario: Redução com vários códigos

- **GIVEN** duas rotas completas confirmadas e o comando para deixar uma
- **WHEN** o comando não diz qual código permanece
- **THEN** o sistema pergunta o código
- **AND** não altera a operação ainda

### Requirement: Ajuste de rota compartilhada

**Tipo**: Requisito funcional

O comando de ajustar compartilhada SHALL definir a quantidade absoluta de rotas compartilhadas da operação resolvida, sem converter rotas completas salvo quando o pedido disser explicitamente que a rota completa passa a ser compartilhada.

#### Scenario: Inclusão de compartilhada

- **GIVEN** o comando autorizado "/ajustar douglas compartilhada=1" e uma única data resolvida
- **WHEN** já existe uma rota completa distinta
- **THEN** a compartilhada é acrescentada na quantidade pedida
- **AND** a completa não é removida automaticamente

#### Scenario: Frase que substitui a modalidade

- **GIVEN** a frase autorizada de que a escala de ontem foi rota compartilhada
- **WHEN** existe uma única operação ontem
- **THEN** o sistema mostra o resultado proposto, com completas e compartilhadas resultantes
- **AND** só grava depois da confirmação do administrador

### Requirement: Ajuste de paradas e quilometragem

**Tipo**: Requisito funcional

O comando de paradas SHALL definir a quantidade inteira do dia. O comando de quilometragem SHALL definir o valor informado manualmente. Nenhum dos dois SHALL alterar o pagamento do motorista.

#### Scenario: Paradas do dia

- **GIVEN** o comando autorizado "/ajustar paradas=95" com uma única operação resolvida
- **WHEN** ele é executado
- **THEN** a quantidade do dia passa a 95
- **AND** o indicador é recalculado pelas faixas
- **AND** o pagamento do motorista permanece o das rotas

#### Scenario: Quilometragem do dia

- **GIVEN** o comando autorizado "/ajustar km=180" com uma única operação resolvida
- **WHEN** ele é executado
- **THEN** a quilometragem do dia fica 180 km com origem manual
- **AND** a tabela de distâncias não muda

### Requirement: Ajuste de combustível

**Tipo**: Requisito funcional

O comando SHALL definir o combustível em reais de um dia. Sem data, SHALL aplicar o valor à operação já resolvida. O combustível do dia começa em R$ 90,00. O comando MUST NOT alterar o pagamento do motorista.

#### Scenario: Combustível do dia resolvido

- **GIVEN** o comando autorizado "/ajustar combustivel=90" na operação de 17/11/2026
- **WHEN** ele é executado
- **THEN** o combustível desse dia fica R$ 90,00
- **AND** o lucro do dia é recalculado

#### Scenario: Combustível de outra data

- **GIVEN** o comando autorizado "/ajustar combustivel=80 data=18/11"
- **WHEN** ele é executado
- **THEN** somente 18/11/2026 passa a R$ 80,00 de combustível
- **AND** 17/11/2026 permanece com o valor que já tinha

### Requirement: Manutenção

**Tipo**: Requisito funcional

O comando `/manutencao`, com ou sem acento, SHALL registrar descrição e valor em reais. Sem data, SHALL usar o dia já resolvido. Se o parecer desse dia já foi publicado, SHALL editar essa mensagem e recalcular o lucro. Se o dia não tiver rota, SHALL publicar no grupo de controle somente a manutenção.

#### Scenario: Manutenção em dia com rota

- **GIVEN** o comando autorizado `/manutencao "Troca de Óleo" 200,00` em 17/11/2026
- **AND** o parecer desse dia já está no grupo de controle
- **WHEN** ele é executado
- **THEN** a mensagem publicada é editada e passa a incluir Troca de Óleo por R$ 200,00
- **AND** o lucro do dia desconta esses R$ 200,00

#### Scenario: Manutenção em dia sem rota

- **GIVEN** o comando autorizado `/manutencao "Troca de Óleo" 200,00 data=18/11`
- **AND** 18/11/2026 não tem rota
- **WHEN** ele é executado
- **THEN** o grupo de controle recebe somente essa manutenção
- **AND** nenhuma mensagem vai ao grupo de origem

### Requirement: PNR

**Tipo**: Requisito funcional

O comando `/pnr` SHALL ser lançado no grupo de controle quando o administrador receber o faturamento da ALC. SHALL descontar o valor na quinzena desse faturamento. Cada comando soma um desconto. MUST NOT ler PNR na escala diária nem alterar o valor de cada rota. Quinzena já fechada SHALL gerar nova versão do demonstrativo.

#### Scenario: Desconto da quinzena aberta

- **GIVEN** o comando autorizado "/pnr 30,00" no grupo de controle
- **AND** a quinzena de 16/11/2026 a 30/11/2026 está aberta e as rotas somam R$ 100,00
- **WHEN** ele é executado
- **THEN** a quinzena passa a ter R$ 30,00 de PNR
- **AND** o total a receber do Douglas fica R$ 70,00

#### Scenario: Faturamento da ALC depois do fechamento

- **GIVEN** a quinzena já fechada com total de R$ 100,00 e PNR zero
- **WHEN** o administrador recebe o faturamento da ALC e envia "/pnr 30,00" no grupo de controle
- **THEN** o total revisado fica R$ 70,00
- **AND** a versão anterior não é somada à nova

### Requirement: Resolução da data

**Tipo**: Regra de negócio

Comando sem data SHALL usar a operação não ambígua do motorista. "Hoje" e "ontem" SHALL usar o fuso America/Sao_Paulo. Se houver mais de uma possibilidade, o sistema SHALL pedir a data e não gravar.

#### Scenario: Ontem inequívoco

- **GIVEN** uma frase autorizada que corrige ontem
- **AND** uma única operação do motorista na data de ontem
- **WHEN** o pedido é interpretado
- **THEN** a data alvo é o dia anterior no fuso America/Sao_Paulo

#### Scenario: Data não informada e vários registros

- **GIVEN** um ajuste sem data e mais de uma operação possível
- **WHEN** o comando é recebido
- **THEN** o sistema pede a data
- **AND** não altera registros

### Requirement: Consultas

**Tipo**: Requisito funcional

Consultar hoje SHALL mostrar as operações da data atual no fuso America/Sao_Paulo. Consultar o motorista SHALL mostrar a quinzena corrente e o estado de hoje. Consultar quinzena SHALL mostrar o período corrente. Consultar rota SHALL mostrar o cadastro e as execuções recentes, sem pagamento de outro motorista.

#### Scenario: Consulta de hoje

- **GIVEN** o comando autorizado "/consultar hoje"
- **WHEN** a data local é 17/11/2026
- **THEN** a resposta cobre somente operações dessa data
- **AND** os valores vêm do backend

#### Scenario: Consulta da quinzena no dia 15

- **GIVEN** o comando autorizado "/consultar quinzena" em 15/11/2026
- **WHEN** a consulta é respondida
- **THEN** o período informado é de 01/11/2026 a 15/11/2026
- **AND** o total é o pagamento do motorista, separado do indicador de paradas

#### Scenario: Consulta da quinzena no dia 16

- **GIVEN** o comando autorizado "/consultar quinzena" em 16/11/2026
- **WHEN** a consulta é respondida
- **THEN** o período informado começa em 16/11/2026 e termina no último dia desse mês

#### Scenario: Consulta de rota

- **GIVEN** o comando autorizado "/consultar rota A24_PM1"
- **WHEN** a rota existe
- **THEN** a resposta mostra código, cidades e execuções recentes
- **AND** não revela pagamento de motorista que não seja o alvo da consulta autorizada

### Requirement: Fechamento e reenvio por comando

**Tipo**: Requisito funcional

O comando de fechar quinzena SHALL acionar o mesmo fechamento do agendamento para o período corrente e SHALL declarar quando for antecipado em relação às 17:00 do dia de fechamento. O comando de reenviar PDF SHALL reenviar a versão consolidada pedida, ou perguntar o período se houver mais de um.

#### Scenario: Fechamento manual no dia 15

- **GIVEN** o comando autorizado "/fechar quinzena" no dia 15, antes ou depois das 17:00
- **WHEN** não há pendência que bloqueie
- **THEN** o período de 1 a 15 é consolidado pelo fluxo oficial
- **AND** um disparo anterior ao horário informa que o fechamento foi manual

#### Scenario: Reenvio sem período

- **GIVEN** mais de um demonstrativo consolidado e o comando "/reenviar pdf"
- **WHEN** o período não é informado
- **THEN** o sistema pergunta qual período reenviar
- **AND** não envia um documento escolhido ao acaso

### Requirement: Cadastro e ajuda

**Tipo**: Requisito funcional

O comando de cadastrar motorista SHALL conduzir o administrador pelos campos obrigatórios e SHALL exigir os dois valores de rota antes de ativar. O comando de ajuda SHALL listar os comandos disponíveis e informar que os valores são calculados pelo sistema.

#### Scenario: Cadastro guiado incompleto

- **GIVEN** o comando autorizado "/cadastrar motorista"
- **WHEN** o administrador ainda não informou os valores das modalidades
- **THEN** o motorista não fica ativo
- **AND** o sistema pede os campos que faltam

#### Scenario: Ajuda

- **GIVEN** o comando autorizado "/ajuda"
- **WHEN** a resposta é enviada
- **THEN** ela lista os comandos iniciais de ajuste, consulta, fechamento, reenvio, cadastro e ajuda
- **AND** não promete alterar valor fora do backend

### Requirement: Linguagem natural equivalente

**Tipo**: Requisito funcional

O sistema SHALL aceitar frases equivalentes aos comandos, como informar que o motorista fará somente uma rota, corrigir a escala de ontem para compartilhada ou perguntar quantas rotas ele fez na quinzena. A frase SHALL passar pela mesma autorização e pelas mesmas regras do comando correspondente.

#### Scenario: Uma rota hoje

- **GIVEN** a frase autorizada "Hoje o Douglas vai fazer somente uma rota."
- **AND** uma única operação de hoje
- **WHEN** a frase é interpretada
- **THEN** o efeito proposto é uma rota completa nessa data
- **AND** o backend calcula o valor

#### Scenario: Pergunta da quinzena

- **GIVEN** a frase autorizada "Quantas rotas o Douglas fez nesta quinzena?"
- **WHEN** ela é interpretada
- **THEN** a resposta usa a consulta oficial do período corrente
- **AND** não altera registros

## Exceções cobertas

- Remetente não administrador não altera dados.
- Redução de rotas sem código não grava sozinha.
- Substituição de modalidade por frase pede confirmação.
- Vários alvos ou vários PDFs exigem escolha.
- Cadastro sem tarifas não fica ativo.
- Consulta não mistura pagamento de outro motorista.
