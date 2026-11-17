# Pagamentos do motorista

## Purpose

Calcular e guardar o pagamento do motorista exclusivamente por rota completa e rota compartilhada, com histórico diário, ajuste sobre o mesmo registro e separação do faturamento da operação.

## Objetivo

O motor de regras aplica a tarifa cadastrada do motorista. Uma aparição isolada é rota completa; aparição com outra pessoa na mesma rota é compartilhada; ausência só existe quando a leitura confiável está completa. Dúvida não gera pagamento.

## Dependências

- `driver-management`: tarifas, monitoramento e reconhecimento.
- `image-processing`: leitura, confiança e data.
- `vehicle-management`: veículo da chave diária.
- `route-management`: código observado, sem transformar código em tarifa.
- `stops-calculation` e `mileage-calculation`: fatos separados, que não entram neste total.
- `financial-reports`: soma somente operações confirmadas.
- `audit-and-history`: histórico de ajuste.
- `database-management`: transação, decimal e unicidade.

## Requirements

### Requirement: Base do pagamento

**Tipo**: Regra de negócio

O pagamento SHALL ser a soma das rotas completas e compartilhadas confirmadas, usando a tarifa do motorista. O sistema MUST NOT incluir remuneração por paradas, quilometragem, faturamento bruto, receita da operação, custo do veículo ou pagamento de outro motorista.

#### Scenario: Consulta do valor a pagar

- **GIVEN** um dia com rotas confirmadas, indicador de paradas e quilometragem
- **WHEN** o pagamento do motorista é consultado
- **THEN** o total contém somente as linhas de rota completa e compartilhada

### Requirement: Snapshot da tarifa

**Tipo**: Regra de negócio

Ao confirmar a operação, o sistema SHALL gravar o valor unitário usado. Alteração posterior no cadastro MUST NOT mudar operação confirmada ou consolidada. Ajuste de quantidade SHALL reutilizar o valor unitário já gravado na operação.

#### Scenario: Tarifa muda depois

- **GIVEN** uma operação confirmada com rota completa a R$ 100,00
- **WHEN** o cadastro do motorista passa a outro valor
- **THEN** essa operação continua a R$ 100,00

#### Scenario: Ajuste de quantidade

- **GIVEN** uma operação confirmada com unitário de rota completa já gravado
- **WHEN** o administrador autorizado altera a quantidade de rotas completas
- **THEN** o novo total usa esse unitário gravado
- **AND** não busca uma tarifa diferente inventada na hora

### Requirement: Rota completa

**Tipo**: Regra de negócio

Cada vez que o nome do motorista monitorado aparece sozinho, o sistema SHALL gerar uma linha completa. A quantidade de cidades dessa aparição MUST NOT multiplicar o pagamento. Com a tarifa inicial, uma aparição vale R$ 100,00 e duas aparições valem R$ 200,00.

#### Scenario: Uma aparição

- **GIVEN** Douglas, com a tarifa inicial, aparece sozinho em uma única rota
- **WHEN** a operação é confirmada
- **THEN** existe uma linha completa de R$ 100,00
- **AND** o total do dia é R$ 100,00

#### Scenario: Cidades não multiplicam

- **GIVEN** o nome Douglas aparece uma única vez, sozinho, com quatro cidades
- **WHEN** a operação é confirmada com a tarifa inicial
- **THEN** existe uma linha completa de R$ 100,00
- **AND** as quatro cidades não geram quatro pagamentos

#### Scenario: Referência de uma rota

- **GIVEN** a leitura confiável, ou a confirmação do administrador, de docs/referencias/escala-01-uma-rota.png
- **AND** Douglas aparece somente em D9_PM1, cidade Congonhinhas
- **WHEN** a operação é confirmada com a tarifa inicial
- **THEN** o pagamento é uma rota completa de R$ 100,00

#### Scenario: Três rotas distintas

- **GIVEN** o nome do motorista aparece sozinho três vezes
- **WHEN** a operação é confirmada com a tarifa inicial de R$ 100,00
- **THEN** existem três linhas completas
- **AND** o total do dia é R$ 300,00

#### Scenario: Referência de duas rotas

- **GIVEN** a leitura confiável de docs/referencias/escala-02-duas-rotas.png
- **AND** Douglas aparece sozinho em C25_PM1 e em B15_PM1
- **WHEN** a operação é confirmada com a tarifa inicial
- **THEN** existem duas linhas completas
- **AND** o total do dia é R$ 200,00

### Requirement: Rota compartilhada

**Tipo**: Regra de negócio

Quando o motorista monitorado e ao menos outra pessoa estiverem na mesma aparição, o sistema SHALL gerar uma linha compartilhada. Com a tarifa inicial, o valor é R$ 50,00 uma vez. Várias cidades ou várias outras pessoas nessa aparição MUST NOT multiplicar esse valor.

#### Scenario: Douglas e outra pessoa

- **GIVEN** uma rota cuja célula traz Douglas e outra pessoa
- **WHEN** a operação é confirmada com a tarifa inicial
- **THEN** a linha é compartilhada no valor de R$ 50,00
- **AND** não é criada outra linha completa dessa mesma rota

#### Scenario: Referência da rota dividida

- **GIVEN** a célula "Wesley e Douglas" na rota B14_PM1 de docs/referencias/escala-03-rota-dividida.png
- **AND** as cidades Ribeirão do Pinhal e Trolândia
- **WHEN** essa atribuição é confirmada com a tarifa inicial
- **THEN** ela vale uma rota compartilhada de R$ 50,00
- **AND** as duas cidades não geram outra cobrança

#### Scenario: Três pessoas na mesma rota

- **GIVEN** Douglas e duas outras pessoas na mesma rota
- **WHEN** a leitura é confiável quanto ao compartilhamento
- **THEN** Douglas recebe uma única linha compartilhada
- **AND** não é aplicada uma terceira tarifa

### Requirement: Combinação no mesmo dia

**Tipo**: Regra de negócio

Rotas completas e compartilhadas do mesmo dia SHALL ser somadas. Cada modalidade SHALL usar a própria tarifa gravada.

#### Scenario: Uma completa e uma compartilhada

- **GIVEN** uma rota completa e outra compartilhada confirmadas no mesmo dia
- **AND** as tarifas iniciais de R$ 100,00 e R$ 50,00
- **WHEN** o total é calculado
- **THEN** o pagamento do dia é R$ 150,00

#### Scenario: Referência da terceira imagem

- **GIVEN** a confirmação de docs/referencias/escala-03-rota-dividida.png
- **AND** Douglas sozinho em A27_PM1, com quatro cidades
- **AND** Wesley e Douglas em B14_PM1, com Ribeirão do Pinhal e Trolândia
- **WHEN** o pagamento é confirmado com as tarifas iniciais
- **THEN** A27_PM1 vale R$ 100,00 uma vez
- **AND** B14_PM1 vale R$ 50,00 uma vez
- **AND** o total do dia é R$ 150,00
- **AND** as cidades não multiplicam o valor

### Requirement: Repetição do mesmo código

**Tipo**: Exceção

O sistema MUST NOT pagar duas vezes o mesmo código, na mesma data e para o mesmo motorista, quando a repetição não estiver confirmada como duas execuções distintas. A dúvida SHALL ficar aguardando confirmação.

#### Scenario: Mesmo código em duas linhas

- **GIVEN** o mesmo código aparece duas vezes para o mesmo motorista sem evidência confiável de duas execuções
- **WHEN** a validação ocorre
- **THEN** a operação fica aguardando confirmação
- **AND** o total de R$ 200,00 não é gerado automaticamente

### Requirement: Ausência confirmada

**Tipo**: Regra de negócio

Quando a imagem for confiável, a escala estiver completa e o motorista monitorado não aparecer, o sistema SHALL registrar não escalado, zero rotas e R$ 0,00. Esse dia MUST NOT gerar linha de pagamento.

#### Scenario: Douglas não aparece

- **GIVEN** uma escala completa e confiável sem Douglas
- **WHEN** a operação é registrada
- **THEN** o estado é não escalado
- **AND** a quantidade de rotas é zero
- **AND** o valor a pagar é R$ 0,00
- **AND** não há linha pagável nesse dia

### Requirement: Dúvida não gera pagamento

**Tipo**: Exceção

Leitura em dúvida, escala incompleta ou tipo de rota indefinido SHALL permanecer aguardando confirmação, sem pagamento definitivo e sem estado de não escalado.

#### Scenario: Tipo indefinido

- **GIVEN** dúvida se o motorista está sozinho ou acompanhado
- **WHEN** o backend valida a leitura
- **THEN** não existe pagamento definitivo
- **AND** o dia não é registrado como não escalado

### Requirement: Dia sem mensagem

**Tipo**: Regra de negócio

Ausência de imagem recebida MUST NOT ser registrada automaticamente como não escalado nem como pagamento zero. O dia SHALL aparecer em consulta como sem escala recebida até que uma escala chegue ou um administrador classifique o dia.

#### Scenario: Nenhuma mensagem na data

- **GIVEN** um dia do período sem mensagem de escala
- **WHEN** o pagamento desse dia é consultado
- **THEN** não existe operação de não escalado criada automaticamente
- **AND** não existe valor a pagar gerado para preencher o dia

### Requirement: Ajuste do registro original

**Tipo**: Regra de negócio

Ajuste autorizado SHALL atualizar a mesma operação da data, do motorista e do veículo, sem criar outra operação. O sistema SHALL guardar o estado anterior. Se aumentar a quantidade sem informar códigos, SHALL registrar os códigos como pendentes e ainda assim aplicar a quantidade confirmada pelo administrador.

#### Scenario: Redução para uma rota

- **GIVEN** uma operação confirmada com duas rotas completas
- **WHEN** o administrador autorizado ajusta a quantidade de rotas completas para uma e identifica a rota mantida
- **THEN** a mesma operação passa a ter uma linha completa
- **AND** o histórico conserva as duas linhas anteriores

#### Scenario: Quantidade sem código

- **GIVEN** uma operação do motorista em uma data identificada
- **WHEN** o administrador autorizado define uma rota completa sem informar o código
- **THEN** a operação fica com uma linha completa
- **AND** o código permanece pendente
- **AND** nenhuma segunda operação é criada

### Requirement: Data ambígua do ajuste

**Tipo**: Exceção

Se houver mais de uma operação possível para o ajuste, o sistema SHALL pedir a data e MUST NOT escolher sozinho.

#### Scenario: Mais de uma data em aberto

- **GIVEN** duas operações do motorista que poderiam receber o ajuste
- **WHEN** o pedido não identifica a data
- **THEN** nenhuma das duas é alterada
- **AND** o sistema solicita a data

### Requirement: Unicidade e transação

**Tipo**: Requisito não funcional

O sistema SHALL manter no máximo uma operação por data, motorista e veículo, e SHALL gravar pagamento, linhas e histórico na mesma transação. Falha no meio SHALL deixar o estado anterior intacto.

#### Scenario: Falha durante o ajuste

- **GIVEN** um ajuste que falha antes de concluir a transação
- **WHEN** a operação é consultada
- **THEN** permanecem o total e as linhas anteriores
- **AND** não aparece uma operação duplicada

## Exceções cobertas

- Mesmo código repetido não gera pagamento dobrado sem confirmação.
- Dúvida não vira ausência nem pagamento.
- Dia sem mensagem não vira zero automático.
- Ajuste ambíguo não escolhe registro.
- Falha transacional não deixa pagamento parcial.
- Compartilhamento com várias pessoas não cria tarifa nova.
