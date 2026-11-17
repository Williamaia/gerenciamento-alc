# Agente de IA

## Purpose

Interpretar mensagens, comandos e contexto operacional em português e pedir ao backend ações estruturadas, sem calcular dinheiro, sem inventar dado ausente e sem usar a memória do modelo como registro oficial.

## Objetivo

O agente é a interface entre o WhatsApp e o backend. Ele entende intenção, escolhe a ação e formula a resposta com os dados que o backend devolve. Quem valida, calcula, autoriza e persiste é o backend.

## Dependências

- `whatsapp-integration`: eventos, mídias e envios.
- `image-processing`: interpretação estruturada da escala.
- `whatsapp-commands`: comandos e linguagem natural.
- `driver-payments` e `financial-reports`: fatos financeiros calculados pelo backend.
- `database-management`: leitura oficial antes de responder histórico.
- `security-and-permissions`: autorização do remetente e do grupo.

## Requirements

### Requirement: Separação entre agente e backend

**Tipo**: Regra de negócio

O agente SHALL limitar-se a interpretar a entrada e solicitar uma ação estruturada. O backend SHALL validar, aplicar regra, calcular, persistir e autorizar. O agente MUST NOT gravar pagamento, quilometragem oficial ou fechamento por conta própria.

#### Scenario: Pedido de ajuste

- **GIVEN** um administrador pede para corrigir as rotas de um motorista
- **WHEN** o agente compreende o pedido
- **THEN** ele envia ao backend a ação, a data candidata, o motorista e as quantidades entendidas
- **AND** somente o backend altera o registro e devolve o valor calculado

### Requirement: Proibição de valor inventado

**Tipo**: Regra de negócio

O agente MUST NOT determinar, estimar ou inventar valor financeiro. Todo valor exibido SHALL ser o valor devolvido pelo motor de regras do backend.

#### Scenario: Pergunta sobre pagamento

- **GIVEN** uma pergunta sobre quanto o motorista tem a receber
- **WHEN** o agente responde
- **THEN** o total, as quantidades e os valores unitários são os retornados pelo backend
- **AND** a resposta não contém valor produzido apenas pelo modelo

#### Scenario: Backend recusa a ação

- **GIVEN** uma ação rejeitada pelo backend
- **WHEN** o agente fala com o administrador
- **THEN** ele informa o motivo devolvido pelo backend
- **AND** não confirma a alteração como se tivesse sido aplicada

### Requirement: Fonte oficial dos fatos

**Tipo**: Regra de negócio

Antes de responder fato histórico ou alterar registro, o agente SHALL consultar o estado oficial no PostgreSQL por meio do backend. A memória interna do modelo MUST NOT ser a fonte oficial.

#### Scenario: Consulta de quinzena

- **GIVEN** uma conversa anterior que mencionava outra quantidade de rotas
- **WHEN** o administrador pergunta o total da quinzena
- **THEN** o agente responde com a consulta atual do backend
- **AND** não reaproveita o número lembrado pelo modelo se ele divergir do registro

### Requirement: Escopo de interação

**Tipo**: Regra de negócio

O agente SHALL processar o grupo de origem, o grupo de controle, a conversa particular de administrador e o pedido de paradas ao motorista. No grupo de origem, SHALL apenas receber escalas. Na conversa do motorista, SHALL apenas receber a quantidade pedida. MUST NOT publicar resumo, comando ou conversa no grupo de origem.

#### Scenario: Escala no grupo de origem

- **GIVEN** uma imagem de escala no grupo de origem
- **WHEN** o agente a reconhece
- **THEN** pede o processamento ao backend
- **AND** não envia mensagem de volta ao grupo de origem

#### Scenario: Comando no grupo de origem

- **GIVEN** um comando administrativo escrito no grupo de origem
- **WHEN** o agente o lê
- **THEN** não executa alteração financeira
- **AND** não responde nesse grupo

### Requirement: Pedido de paradas ao motorista

**Tipo**: Regra de negócio

Às 08:00 em America/Sao_Paulo, o agente SHALL enviar uma única mensagem ao motorista pedindo as paradas de cada rota e SHALL identificar-se como frota-plus-agent. SHALL guardar a quantidade respondida. MUST NOT responder outra mensagem nessa conversa. O parecer do dia SHALL ir ao grupo de controle. O demonstrativo da quinzena continua no dia 15 e no último dia.

#### Scenario: Douglas informa as paradas

- **GIVEN** o pedido das 08:00 já enviado a Douglas
- **WHEN** ele responde a quantidade de paradas
- **THEN** essa quantidade fica registrada
- **AND** o agente não envia resposta de volta
- **AND** o parecer segue para o grupo de controle

#### Scenario: Outra mensagem do motorista

- **GIVEN** o pedido de paradas já foi feito
- **WHEN** Douglas envia qualquer outra mensagem
- **THEN** o agente não responde

### Requirement: Dúvida e confirmação

**Tipo**: Regra de negócio

O agente SHALL pedir confirmação quando a data, o motorista, o tipo da rota ou o registro alvo forem ambíguos. SHALL apresentar o rascunho devolvido pelo backend e MUST NOT tratar silêncio ou dúvida como confirmação.

#### Scenario: Duas escalas possíveis

- **GIVEN** um pedido de ajuste que corresponde a mais de uma data
- **WHEN** o agente vai executar a ação
- **THEN** pergunta qual data deve ser alterada
- **AND** nenhuma operação é alterada até a resposta autorizada

### Requirement: Publicação e alerta

**Tipo**: Requisito funcional

O agente SHALL publicar resumo operacional somente depois que o backend confirmar a persistência. SHALL informar o administrador sobre falha de interpretação, mídia, conexão ou fechamento bloqueado, usando o motivo oficial.

#### Scenario: Resumo após gravação

- **GIVEN** o backend persistiu a operação do dia
- **WHEN** o agente comunica o resultado
- **THEN** o texto publicado usa somente os campos persistidos
- **AND** o envio ocorre no grupo de controle

#### Scenario: Problema operacional

- **GIVEN** uma imagem que não pôde ser interpretada
- **WHEN** o backend marca a pendência
- **THEN** o administrador recebe o motivo
- **AND** é pedido que ele leia a imagem e confirme
- **AND** a mensagem não traz rota, cidade ou valor de palpite
- **AND** o motorista não é declarado ausente

### Requirement: Fechamento pedido pelo agente

**Tipo**: Requisito funcional

O agente SHALL tratar pedido de fechamento como solicitação ao backend. O backend MUST decidir se consolida, bloqueia ou reenvia. O agente MUST NOT declarar a quinzena fechada sem essa decisão.

#### Scenario: Fechamento bloqueado

- **GIVEN** uma escala do período ainda aguardando confirmação
- **WHEN** o administrador pede o fechamento
- **THEN** o agente informa o bloqueio e as pendências devolvidas pelo backend
- **AND** não anuncia um total consolidado

### Requirement: Linguagem natural

**Tipo**: Requisito funcional

O agente SHALL compreender português do Brasil, comandos estruturados e pedidos em linguagem natural sobre consulta, correção e fechamento. A ação resultante SHALL ser uma das operações permitidas ao backend.

#### Scenario: Correção em frase

- **GIVEN** a mensagem "Corrige a escala de ontem, ele fez rota compartilhada."
- **WHEN** há uma única operação do motorista na data de ontem no fuso America/Sao_Paulo
- **THEN** o agente submete a correção dessa data ao backend
- **AND** só confirma a mudança depois da resposta do backend

#### Scenario: Frase sem ação permitida

- **GIVEN** um pedido para alterar faturamento da empresa ou inventar uma distância
- **WHEN** o agente interpreta a frase
- **THEN** ele não cria ação financeira fora das operações permitidas
- **AND** informa que não pode atender daquela forma

## Exceções cobertas

- Valor produzido só pelo modelo não pode ser exibido como oficial.
- Comando no grupo de origem não altera dados.
- Ambiguidade não é confirmação.
- Falha de leitura não vira ausência do motorista.
- Fechamento sem decisão do backend não é anunciado como concluído.
