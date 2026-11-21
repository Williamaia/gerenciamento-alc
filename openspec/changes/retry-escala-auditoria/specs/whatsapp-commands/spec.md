# Spec Delta

## ADDED Requirements

### Requirement: Nova leitura da escala

**Tipo**: Requisito funcional

O comando `/retry` no grupo de controle SHALL recomeçar o caminho de uma escala recém-chegada, sem reaproveitar a leitura anterior: baixar o arquivo de novo, ler a imagem com a mesma leitura, resolver a data pelo texto da mensagem e gravar o que for confiável. SHALL aceitar o comando do número conectado. MUST NOT gravar palpite, MUST NOT alterar parada já informada e MUST NOT responder no grupo de origem.

#### Scenario: Número conectado pede de novo

- **GIVEN** uma imagem de escala ainda não gravada
- **AND** o número conectado escreve "/retry" no grupo de controle
- **WHEN** o evento chega marcado como mensagem da própria sessão
- **THEN** o arquivo é baixado de novo
- **AND** a imagem passa pela mesma leitura de uma escala recém-chegada
- **AND** a leitura anterior não é reaproveitada

#### Scenario: Leitura confiável

- **GIVEN** a nova leitura traz data, códigos, cidades e compartilhamento com confiança
- **WHEN** a tentativa termina
- **THEN** esses dados ficam gravados como se a escala tivesse acabado de chegar
- **AND** a imagem deixa de estar pendente
- **AND** as paradas continuam ausentes até o motorista informar
- **AND** a quilometragem segue o caminho normal, depois das paradas
- **AND** o grupo de controle recebe a data e os códigos, sem valor
- **AND** o pedido de paradas segue o horário já definido
- **AND** o grupo de origem não recebe mensagem

#### Scenario: Leitura ainda falha

- **GIVEN** a nova leitura não é confiável
- **WHEN** a tentativa termina
- **THEN** nenhuma rota é gravada
- **AND** o grupo de controle não recebe o erro
- **AND** o grupo de auditoria recebe a falha
- **AND** o aviso diz que o `/retry` não resolveu e pede o endpoint manual de escala

#### Scenario: Nada pendente

- **GIVEN** não há imagem de escala pendente
- **WHEN** "/retry" chega no grupo de controle
- **THEN** o grupo de controle é informado de que não há foto para tentar
- **AND** nenhum dia é alterado

#### Scenario: Paradas já informadas

- **GIVEN** o dia da imagem pendente já tem paradas informadas
- **WHEN** "/retry" é executado
- **THEN** as paradas e as rotas desse dia permanecem
- **AND** nenhuma rota nova é gravada

#### Scenario: Comando no grupo de origem

- **GIVEN** "/retry" escrito no grupo de origem
- **WHEN** o comando chega
- **THEN** nenhuma imagem é relida
- **AND** o grupo de origem não recebe resposta
