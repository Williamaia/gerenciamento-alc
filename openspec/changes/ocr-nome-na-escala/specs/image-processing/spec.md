# Spec Delta

## ADDED Requirements

### Requirement: Bloco da rota no OCR

**Tipo**: Regra de negócio

O sistema SHALL ler a foto só por OCR e percorrer o texto inteiro. validaCidade SHALL responder sim só para município do Paraná. O bloco abre só na linha Douglas, quando ela não é cidade. A linha que contém PM1 é o código. As linhas seguintes com validaCidade sim são as cidades. A primeira linha que não é cidade fecha o bloco. Cada bloco dele SHALL ser uma rota. Outro nome MUST NOT gerar rota. MUST NOT chamar o modelo. Sem Douglas, MUST NOT gravar rota nem enviar mensagem.

#### Scenario: Douglas até a linha que não é cidade

- **GIVEN** as linhas Douglas, exemplo_PM1, Congonhinhas, Nova Fatima e Nikolas
- **WHEN** validaCidade percorre as linhas
- **THEN** Douglas não é cidade e está escalado
- **AND** a rota é exemplo_PM1
- **AND** as cidades são Congonhinhas e Nova Fátima
- **AND** Nikolas não é cidade e o bloco fecha

#### Scenario: Nome em dois blocos

- **GIVEN** Douglas aparece sozinho em dois blocos
- **WHEN** o dia é calculado
- **THEN** existem duas rotas completas
- **AND** o pagamento do dia é o de duas rotas completas

#### Scenario: Nome junto de outra pessoa

- **GIVEN** uma linha com Douglas e outra pessoa, um código e cidades, e depois outro nome
- **WHEN** o bloco é lido
- **THEN** existe uma rota compartilhada
- **AND** essa linha não conta como duas aparições

#### Scenario: Escala sem o nome

- **GIVEN** o OCR da foto devolve a tabela e o texto não contém Douglas
- **WHEN** a leitura termina
- **THEN** o modelo de visão não é chamado
- **AND** nenhuma rota é gravada para ele
- **AND** nenhuma mensagem é enviada a ele
- **AND** a leitura não pede `/retry` nem o endpoint manual

#### Scenario: OCR sem texto

- **GIVEN** o OCR não devolve texto
- **WHEN** a leitura termina
- **THEN** a foto fica como leitura sem confiança
- **AND** o modelo de visão não é chamado
