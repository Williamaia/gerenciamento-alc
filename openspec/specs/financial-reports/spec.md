# Relatórios financeiros

## Purpose

Publicar o resumo operacional no grupo de controle, gerar o demonstrativo somente com o pagamento do motorista e consolidar a quinzena sem duplicar lançamento.

## Objetivo

O resumo mostra operação e pagamento separados. O PDF leva ao motorista apenas rotas, modalidades e valores devidos. O fechamento é idempotente, bloqueia pendência que altere o pagamento e guarda versão revisada quando houver correção posterior.

## Dependências

- `driver-payments`: valores e estados das operações.
- `stops-calculation` e `mileage-calculation`: campos do resumo, fora do PDF.
- `task-scheduling`: dispara o fechamento automático.
- `whatsapp-commands`: fechamento manual e reenvio.
- `whatsapp-integration`: entrega texto e PDF.
- `audit-and-history`: versões e envios.
- `security-and-permissions`: quem recebe e quem autoriza.

## Requirements

### Requirement: Resumo da operação

**Tipo**: Requisito funcional

Depois de persistir uma escala, o sistema SHALL publicar no grupo de controle a data, o motorista, a quantidade de rotas, os códigos conhecidos, as cidades, a quilometragem, as paradas, o indicador de paradas e o pagamento por rota com o total. O total SHALL ser só o pagamento do motorista.

#### Scenario: Duas rotas completas

- **GIVEN** a operação de Douglas em 17/11/2026 confirmada com A24_PM1 e A11_PM1, cidades lidas, quilometragem oficial e paradas confirmadas
- **AND** duas linhas de R$ 100,00
- **WHEN** o resumo é publicado
- **THEN** a mensagem identifica o Frota Plus, a data, o motorista e as duas rotas
- **AND** o pagamento lista R$ 100,00 e R$ 100,00
- **AND** o total é R$ 200,00
- **AND** o indicador de paradas aparece separado do total

#### Scenario: Campo operacional pendente

- **GIVEN** pagamento confirmado e quilometragem ou paradas pendentes
- **WHEN** o resumo é publicado
- **THEN** o campo pendente aparece como pendente
- **AND** o total do motorista não usa número inventado para completar esse campo

### Requirement: Resumo de não escalado

**Tipo**: Regra de negócio

Para operação não escalada, o sistema SHALL publicar data, motorista, estado não escalado, quantidade zero e pagamento R$ 0,00. MUST NOT listar pagamento de rota nem indicador de paradas como valor devido.

#### Scenario: Motorista fora da escala

- **GIVEN** uma operação não escalada de Douglas em 17/11/2026
- **WHEN** o resumo é publicado
- **THEN** a mensagem informa que ele não está escalado
- **AND** a quantidade de rotas é zero
- **AND** o pagamento é R$ 0,00

### Requirement: Resumo aguardando confirmação

**Tipo**: Exceção

Se a operação aguardar confirmação, o sistema SHALL publicar que o resultado não está confirmado e listar os dados que faltam. MUST NOT apresentar o total como pagamento definitivo.

#### Scenario: Dúvida na leitura

- **GIVEN** uma interpretação persistida em aguardando confirmação
- **WHEN** o resumo é publicado
- **THEN** a mensagem lista as pendências
- **AND** pede ao administrador que leia a imagem e confirme
- **AND** não publica código, cidade ou valor que a leitura não tenha confirmado
- **AND** não declara um total definitivo a pagar

### Requirement: Conteúdo do PDF

**Tipo**: Regra de negócio

O PDF SHALL listar cada dia da quinzena, com rota, tipo e valor. Dia sem rota SHALL aparecer como sem rota e valor zero. O total a receber SHALL ser a soma das rotas menos as PNR do período. O documento SHALL trazer as quantidades, os dias trabalhados e o total.

#### Scenario: Período com três linhas

- **GIVEN** linhas confirmadas de rota completa, completa e compartilhada no período
- **WHEN** o PDF é gerado
- **THEN** o título é "DEMONSTRATIVO DE PAGAMENTO — MOTORISTA"
- **AND** a tabela mostra data, rota, tipo e valor de cada linha
- **AND** o resumo traz as duas quantidades, os dias trabalhados e o total

#### Scenario: Dia com duas rotas

- **GIVEN** um mesmo dia com duas rotas pagáveis
- **WHEN** o PDF é gerado
- **THEN** esse dia contribui com duas linhas
- **AND** conta como um dia trabalhado

### Requirement: Exclusões do PDF

**Tipo**: Regra de negócio

O PDF MUST NOT apresentar faturamento bruto, faturamento da ALC, receita diária, lucro, custo do veículo, pagamento de outro motorista ou remuneração por paradas. Dia sem rota SHALL constar na lista e MUST NOT aumentar o total.

#### Scenario: Dia sem rota no período

- **GIVEN** uma quinzena com um dia de rota e os demais sem rota
- **WHEN** o PDF é gerado
- **THEN** todos os dias do período aparecem
- **AND** o dia sem rota entra com valor zero
- **AND** o total é só a soma das rotas menos as PNR

#### Scenario: Indicador de paradas existente

- **GIVEN** operações com indicador de paradas calculado
- **WHEN** o PDF é gerado
- **THEN** esse indicador não aparece no documento
- **AND** não entra no total a receber

### Requirement: Entrega do PDF

**Tipo**: Requisito funcional

O sistema SHALL salvar o PDF, enviar ao telefone cadastrado do motorista a mensagem do período, registrar data, hora e identificador da mensagem e avisar o grupo de controle. A mensagem ao motorista SHALL informar que o demonstrativo daquele período está pronto e que o documento detalha rotas e valores, identificando o Frota Plus.

#### Scenario: Envio da primeira quinzena

- **GIVEN** um demonstrativo consolidado de 01/11/2026 a 15/11/2026 para Douglas
- **WHEN** a entrega é concluída
- **THEN** Douglas recebe o texto do período e o PDF
- **AND** o grupo de controle é notificado
- **AND** o identificador da mensagem fica registrado

### Requirement: Reenvio

**Tipo**: Regra de negócio

Reenvio autorizado SHALL enviar de novo o PDF da versão já consolidada, registrar novo envio e MUST NOT criar lançamento, versão ou total adicional.

#### Scenario: Pedido de reenvio

- **GIVEN** um fechamento já consolidado e já enviado
- **WHEN** o administrador autorizado pede o reenvio
- **THEN** o mesmo documento da versão atual é enviado novamente
- **AND** o total a pagar do período permanece o mesmo

### Requirement: Períodos de fechamento

**Tipo**: Regra de negócio

O sistema SHALL consolidar, por motorista monitorado, o período do dia 1 ao dia 15 inclusive e o período do dia 16 ao último dia do mês inclusive. A consolidação SHALL considerar apenas operações já registradas, inclusive as do próprio dia de fechamento já confirmadas antes da execução.

#### Scenario: Operação do dia 15

- **GIVEN** uma operação de 15/11 já confirmada antes do fechamento
- **WHEN** o primeiro período é consolidado
- **THEN** essa operação entra no demonstrativo

#### Scenario: Operação do último dia

- **GIVEN** uma operação do último dia do mês já confirmada antes do fechamento
- **WHEN** o segundo período é consolidado
- **THEN** essa operação entra no demonstrativo

### Requirement: Bloqueio por pendência

**Tipo**: Exceção

O sistema SHALL bloquear a consolidação se existir, no período, operação aguardando confirmação ou divergência em que o total não coincida com a soma das linhas. SHALL informar cada pendência ao administrador e MUST NOT enviar PDF como fechamento final.

#### Scenario: Escala ainda em dúvida

- **GIVEN** uma operação do período aguardando confirmação
- **WHEN** o fechamento é disparado
- **THEN** a consolidação não ocorre
- **AND** o administrador recebe a lista de pendências
- **AND** nenhum PDF final é enviado

### Requirement: Imagem ainda não recebida

**Tipo**: Regra de negócio

Dia sem escala recebida MUST NOT ser convertido em ausência nem bloquear, sozinho, a consolidação. O aviso ao administrador SHALL listar esses dias. Escala recebida e ainda não processada ou não confirmada SHALL bloquear.

#### Scenario: Dias sem mensagem

- **GIVEN** um período sem pendência de interpretação e com dias em que nenhuma escala chegou
- **WHEN** o fechamento é disparado
- **THEN** a consolidação pode ocorrer com as operações confirmadas
- **AND** os dias sem mensagem são informados ao administrador
- **AND** nenhum desses dias entra no PDF como não escalado

#### Scenario: Imagem recebida ainda não processada

- **GIVEN** uma imagem de escala do período já recebida e ainda sem resultado confirmado
- **WHEN** o fechamento é disparado
- **THEN** a consolidação fica bloqueada

### Requirement: PNR na quinzena do motorista

**Tipo**: Regra de negócio

PNR SHALL ser pacote perdido ou entregue errado, em reais, informado só quando chegar o faturamento da ALC. A soma das rotas SHALL permanecer. O total a receber SHALL ser essa soma menos as PNR. Se o período já estiver fechado, SHALL sair nova versão, sem somar com a anterior.

#### Scenario: Desconto sobre a soma

- **GIVEN** rotas da quinzena somando R$ 100,00 e uma PNR de R$ 30,00
- **WHEN** o demonstrativo é fechado
- **THEN** a soma das rotas permanece R$ 100,00
- **AND** o total a receber é R$ 70,00

### Requirement: Lucro do dia

**Tipo**: Regra de negócio

O lucro do dia SHALL ser o ganho da Fiorino menos o pagamento do motorista, o combustível e as manutenções desse dia.

#### Scenario: Dia com manutenção

- **GIVEN** ganho da Fiorino de R$ 277,25, pagamento do motorista de R$ 100,00, combustível de R$ 90,00 e manutenção de R$ 200,00
- **WHEN** o lucro do dia é calculado
- **THEN** o lucro é R$ 112,75 negativo

### Requirement: Relatório da Fiorino na quinzena

**Tipo**: Requisito funcional

Ao fechar a quinzena, o sistema SHALL enviar ao grupo de controle cada dia do período, a soma dos ganhos da Fiorino, os pagamentos do motorista já líquidos de PNR, os abastecimentos, as manutenções e o lucro. O lucro SHALL descontar esses três itens dos ganhos.

#### Scenario: Fechamento do período

- **GIVEN** uma quinzena com ganhos, pagamentos diários, abastecimentos e manutenções já registrados
- **WHEN** o fechamento desse período é concluído
- **THEN** o grupo de controle recebe o relatório com esses totais e o lucro
- **AND** o relatório sai no dia 15 e no último dia do mês

### Requirement: Idempotência do fechamento

**Tipo**: Requisito não funcional

Cada fechamento SHALL ter identidade única por motorista, início, fim e versão. Repetir a consolidação da mesma versão SHALL devolver o resultado existente, sem novo lançamento.

#### Scenario: Disparo repetido

- **GIVEN** um período já consolidado na versão 1
- **WHEN** o mesmo fechamento é disparado outra vez sem correção posterior
- **THEN** a versão 1 é reutilizada
- **AND** o total não é lançado de novo

### Requirement: Versão revisada

**Tipo**: Regra de negócio

Correção autorizada depois da consolidação SHALL manter a versão anterior, criar nova versão com o total recalculado e gerar novo PDF. O sistema SHALL enviar a versão nova ao motorista e avisar o administrador. MUST NOT conservar as duas versões como pagamentos somáveis.

#### Scenario: Ajuste depois do fechamento

- **GIVEN** um período já consolidado
- **WHEN** um administrador autorizado corrige uma operação desse período
- **THEN** a versão anterior permanece consultável
- **AND** a nova versão passa a ser o pagamento do período
- **AND** o motorista recebe o PDF revisado
- **AND** a soma das duas versões não vira o valor devido

## Exceções cobertas

- Pendência de confirmação ou conta divergente bloqueia o fechamento.
- Imagem ainda não recebida não vira ausência.
- Imagem recebida e não concluída bloqueia.
- Reenvio e repetição não criam lançamento.
- Versões revisadas não se somam.
- PDF não inclui dia não escalado nem indicador de paradas.
