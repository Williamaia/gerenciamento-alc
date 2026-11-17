# Processamento de imagens

## Purpose

Transformar a imagem de uma escala em representação estruturada e verificável, preservar a data escrita na mensagem e impedir que leitura incompleta vire ausência ou pagamento.

## Objetivo

O processamento lê a tabela, associa cidades à rota correta e devolve campos com confiança. O backend decide o que pode ser confirmado. As três imagens em `docs/referencias/` ilustram o formato inicial e não congelam o desenho.

## Dependências

- `whatsapp-integration`: arquivo e texto da mesma mensagem.
- `ai-agent`: encaminha a interpretação e as dúvidas.
- `driver-management`: casamento de nomes após a extração.
- `route-management`: códigos e cidades observadas, sem obrigar cadastro prévio para a leitura.
- `driver-payments`: só confirma pagamento depois da validação descrita aqui.
- `database-management`: guarda imagem, extração e estado.

## Requirements

### Requirement: Data oficial da mensagem

**Tipo**: Regra de negócio

O sistema SHALL usar como data da operação a data explícita no texto da mesma mensagem da imagem. MUST NOT substituir essa data pela data de recebimento.

#### Scenario: Escala recebida no dia seguinte

- **GIVEN** uma imagem recebida em 18/11/2026
- **AND** o texto da mesma mensagem é "Segue a escala 17/11"
- **WHEN** a data é interpretada
- **THEN** a data proposta da operação é 17/11/2026
- **AND** 18/11/2026 não é gravada como data da operação

#### Scenario: Ano explícito

- **GIVEN** o texto contém 17/11/2025
- **WHEN** a data é interpretada
- **THEN** o ano usado é 2025, mesmo que o recebimento ocorra em outro ano

### Requirement: Ano omitido

**Tipo**: Regra de negócio

Se a data explícita não tiver ano, o sistema SHALL propor o ano da data de recebimento no fuso America/Sao_Paulo. Se a data resultante ficar mais de sete dias no futuro em relação ao recebimento, SHALL exigir confirmação e MUST NOT confirmá-la automaticamente.

#### Scenario: Ano implícito dentro da janela

- **GIVEN** recebimento em 18/11/2026 e texto "17/11"
- **WHEN** a data é interpretada
- **THEN** a data proposta é 17/11/2026
- **AND** ela pode seguir para validação sem pedir ano

#### Scenario: Data implícita distante no futuro

- **GIVEN** recebimento em 02/01/2026 e texto "17/11"
- **WHEN** a data proposta seria 17/11/2026
- **THEN** a interpretação fica aguardando confirmação
- **AND** a data de recebimento não é adotada no lugar

### Requirement: Data ausente ou conflitante

**Tipo**: Exceção

Se a mesma mensagem não tiver data explícita, ou tiver mais de uma data candidata, o sistema SHALL deixar a data vazia e aguardando confirmação. MUST NOT usar a data de recebimento como data oficial.

#### Scenario: Imagem sem data no texto

- **GIVEN** uma imagem de escala sem data no texto da mesma mensagem
- **WHEN** a interpretação termina
- **THEN** a data oficial fica ausente
- **AND** o estado é aguardando confirmação
- **AND** o dia do recebimento não vira data da operação

### Requirement: Extração estruturada

**Tipo**: Requisito funcional

O sistema SHALL produzir motorista conforme lido, código da rota, cidades, paradas quando existirem e indicador de compartilhamento, cada um com confiança. Campo não lido SHALL permanecer vazio.

#### Scenario: Linha completa

- **GIVEN** uma linha legível com motorista, código, cidades e paradas
- **WHEN** a imagem é interpretada com confiança
- **THEN** a representação contém esses campos sem completar dado que não está na imagem

#### Scenario: Paradas não aparecem

- **GIVEN** uma escala legível que não mostra quantidade de paradas
- **WHEN** a interpretação confiável termina
- **THEN** a quantidade de paradas fica vazia
- **AND** o vazio não é convertido em zero

### Requirement: Cidades em linhas seguintes

**Tipo**: Regra de negócio

O sistema SHALL associar cada cidade escrita na mesma linha ou em linha abaixo, sem novo motorista ou código, à rota correspondente. Várias cidades SHALL permanecer na mesma atribuição. SHALL preservar a sequência visual.

#### Scenario: Continuação da mesma rota

- **GIVEN** um código de rota seguido por cidades em linhas inferiores sem novo código
- **WHEN** a tabela é interpretada
- **THEN** essas cidades pertencem àquela rota
- **AND** permanecem na ordem em que aparecem

#### Scenario: Nova rota interrompe a continuação

- **GIVEN** cidades abaixo de uma rota e depois um novo código
- **WHEN** a tabela é interpretada
- **THEN** as cidades anteriores não são atribuídas ao novo código

#### Scenario: Quatro cidades na mesma rota

- **GIVEN** a rota A27_PM1 de docs/referencias/escala-03-rota-dividida.png, com Douglas sozinho
- **AND** as cidades Santa Amélia, Ribeirão do Pinhal, Nova Fátima e Congonhinhas
- **WHEN** a tabela é interpretada com confiança ou confirmada pelo administrador
- **THEN** as quatro cidades pertencem a essa única rota
- **AND** nenhuma cidade vira outra rota do Douglas

### Requirement: Variação de layout

**Tipo**: Requisito não funcional

O sistema SHALL aceitar variação de disposição da tabela. Uma imagem de referência presente no projeto SHALL servir apenas como exemplo inicial. MUST NOT haver um único layout rígido obrigatório para todas as escalas futuras.

#### Scenario: Referência ausente

- **GIVEN** nenhuma imagem de referência anexada ao projeto
- **WHEN** uma escala real é recebida
- **THEN** o sistema ainda tenta a leitura estruturada
- **AND** não rejeita a imagem somente porque o desenho difere de um modelo fixo

#### Scenario: Leitura insuficiente

- **GIVEN** uma imagem cujo desenho não permite separar linhas com segurança
- **WHEN** a interpretação termina
- **THEN** motorista, código, cidade e parada não lidos permanecem vazios
- **AND** nenhum palpite é gravado no lugar
- **AND** o estado é aguardando confirmação
- **AND** nenhum pagamento é confirmado

### Requirement: Exemplos iniciais de escala

**Tipo**: Regra de negócio

O sistema SHALL tratar as três imagens em docs/referencias como exemplos iniciais, não como molde fixo. A leitura SHALL reconhecer motorista, código da rota e cidade mesmo com título de coluna diferente. Dois nomes na mesma célula, ligados por "e", SHALL formar uma única atribuição.

#### Scenario: Uma rota do Douglas

- **GIVEN** a imagem docs/referencias/escala-01-uma-rota.png confirmada pelo administrador ou lida por completo e com confiança
- **WHEN** a linha do motorista monitorado Douglas é registrada
- **THEN** a rota é D9_PM1
- **AND** a cidade é Congonhinhas
- **AND** ele aparece sozinho nessa rota

#### Scenario: Duas rotas do Douglas

- **GIVEN** a imagem docs/referencias/escala-02-duas-rotas.png lida por completo e com confiança
- **WHEN** as linhas do Douglas são extraídas
- **THEN** ele aparece sozinho em C25_PM1 e em B15_PM1
- **AND** a cidade lida nas duas linhas é Nova Fátima

#### Scenario: Terceira imagem, duas atribuições

- **GIVEN** a imagem docs/referencias/escala-03-rota-dividida.png lida com confiança ou confirmada pelo administrador
- **WHEN** as atribuições do Douglas são registradas
- **THEN** existe uma rota completa A27_PM1, com Santa Amélia, Ribeirão do Pinhal, Nova Fátima e Congonhinhas
- **AND** existe uma rota compartilhada B14_PM1, na célula "Wesley e Douglas", com Ribeirão do Pinhal e Trolândia
- **AND** essas cidades não geram os códigos A5_PM1 nem A9_PM1

#### Scenario: Linha que não é rota

- **GIVEN** a linha final dessa terceira imagem, com Everson, o texto "ambulância" e "região de andirá"
- **WHEN** a tabela é interpretada
- **THEN** essa linha não cria rota nem pagamento para o Douglas
- **AND** o texto "ambulância" não é tratado como código de rota

### Requirement: Imagem ruim

**Tipo**: Exceção

Quando a imagem estiver ruim, borrada, cortada ou com trecho ilegível, o sistema MUST NOT preencher motorista, código, cidade, parada ou pagamento com palpite. SHALL pedir ao administrador que leia a imagem e confirme. MUST NOT tratar esse estado como ausência do motorista.

#### Scenario: Código ilegível

- **GIVEN** uma escala em que o código da rota não pode ser lido com segurança
- **WHEN** a interpretação termina
- **THEN** o código permanece vazio
- **AND** nenhum outro código é colocado no lugar
- **AND** o administrador recebe pedido para ler a imagem e confirmar
- **AND** nenhum pagamento é confirmado

#### Scenario: Leitura incerta da primeira referência

- **GIVEN** a imagem docs/referencias/escala-01-uma-rota.png sem leitura segura da linha
- **WHEN** surge um código ou uma cidade diferentes de D9_PM1 e Congonhinhas, ou esses dados sem confiança
- **THEN** o palpite não é gravado
- **AND** o administrador é chamado a ler a imagem e confirmar

### Requirement: Escala completa e ausência

**Tipo**: Regra de negócio

O sistema SHALL marcar um motorista monitorado como não escalado somente quando a leitura for confiável, a escala estiver completa e o nome dele não tiver sido encontrado. Escala ilegível, incompleta ou com região não lida MUST NOT contar como ausência.

#### Scenario: Nome ausente em escala confiável

- **GIVEN** uma escala completa, com todas as linhas legíveis, sem o motorista monitorado
- **WHEN** o backend valida a interpretação
- **THEN** a operação desse motorista nessa data pode ser registrada como não escalado
- **AND** a quantidade de rotas é zero

#### Scenario: Região ilegível

- **GIVEN** uma imagem em que uma linha de motorista não pôde ser lida
- **WHEN** o nome do motorista monitorado não aparece nas linhas lidas
- **THEN** o estado permanece aguardando confirmação
- **AND** o sistema não registra não escalado nem pagamento zero definitivo

### Requirement: Segunda imagem da mesma data

**Tipo**: Exceção

O sistema SHALL impedir que outra imagem da mesma data, motorista e veículo crie uma segunda operação pagável. A nova leitura SHALL abrir revisão pendente até confirmação autorizada.

#### Scenario: Nova foto para data já confirmada

- **GIVEN** uma operação já confirmada para o motorista naquela data
- **WHEN** chega outra imagem com a mesma data oficial
- **THEN** a operação existente não é duplicada
- **AND** a nova leitura fica aguardando confirmação antes de substituir a anterior

### Requirement: Processamento assíncrono

**Tipo**: Requisito não funcional

O sistema SHALL processar imagem fora do ciclo imediato do webhook, com fila persistente, retentativa limitada e reprocessamento idempotente pelo identificador da mensagem.

#### Scenario: Reinício durante a leitura

- **GIVEN** uma imagem aceita na fila e ainda não interpretada
- **WHEN** o processo é reiniciado
- **THEN** a imagem continua disponível para processamento
- **AND** uma conclusão posterior grava um único resultado para aquela mensagem

### Requirement: Validação antes do registro

**Tipo**: Regra de negócio

O backend SHALL validar data, motoristas, rotas, cidades, quantidades e consistência antes de confirmar a operação. Interpretação com dúvida em campo que afete o pagamento SHALL permanecer aguardando confirmação.

#### Scenario: Rota e motorista consistentes

- **GIVEN** uma interpretação confiável com data, motorista reconhecido e rotas distintas
- **WHEN** o backend não encontra contradição
- **THEN** a operação pode ser confirmada
- **AND** os valores nascem do motor de pagamento, não da leitura

#### Scenario: Campo de pagamento em dúvida

- **GIVEN** dúvida sobre se a rota é completa ou compartilhada
- **WHEN** o backend valida a leitura
- **THEN** a operação fica aguardando confirmação
- **AND** nenhum pagamento definitivo é gerado

## Exceções cobertas

- Data ausente, conflitante ou futura demais não é confirmada sozinha.
- Parada ausente não vira zero.
- Layout desconhecido ou ilegível não vira ausência.
- Segunda imagem não cria segunda operação.
- Dúvida sobre tipo da rota bloqueia o pagamento.
- A linha "ambulância" não vira código de rota nem pagamento do Douglas.
- Imagem ruim não recebe motorista, código, cidade, parada ou pagamento de palpite. O administrador lê e confirma.
- Cidades da mesma rota não geram rotas nem pagamentos extras.
