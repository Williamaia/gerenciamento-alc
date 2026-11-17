# Integração WhatsApp

## Purpose

Conectar o número operacional do Frota Plus à Evolution API para receber eventos, baixar mídias, enviar texto e PDF somente a destinos autorizados e recuperar falhas sem perder mensagens.

## Objetivo

A integração é o transporte. Ela identifica origem, remetente, resposta e arquivo, persiste os identificadores e entrega eventos ao agente. Ela não interpreta escala, não calcula pagamento e não decide regra de negócio.

## Dependências

- `security-and-permissions`: autenticidade do webhook, segredos e destinos autorizados.
- `database-management`: persistência de mensagens, fila e deduplicação.
- `audit-and-history`: registro de recebimento, envio e falha.
- `ai-agent`: consome o evento já identificado e persistido.

## Requirements

### Requirement: Recebimento por webhook

**Tipo**: Requisito funcional

O sistema SHALL receber eventos da Evolution API por webhook e persistir o identificador da mensagem fornecido pelo provedor antes de qualquer interpretação.

#### Scenario: Mensagem de grupo persistida

- **GIVEN** um webhook autêntico de mensagem do grupo de origem
- **WHEN** o evento é recebido
- **THEN** a mensagem fica registrada com identificador do provedor, grupo, remetente, data e hora e indicador de mídia
- **AND** o evento segue para processamento sem calcular valor financeiro

#### Scenario: Evento repetido pelo provedor

- **GIVEN** uma mensagem cujo identificador do provedor já foi persistido
- **WHEN** o mesmo evento chega outra vez
- **THEN** o sistema não cria outra mensagem
- **AND** não dispara outro processamento de escala nem outro envio

### Requirement: Identidade da mensagem

**Tipo**: Requisito funcional

O sistema SHALL identificar grupo, remetente, identificador da mensagem e, quando existir, a mensagem respondida. O sistema MUST NOT tratar um grupo não cadastrado como origem ou destino autorizado.

#### Scenario: Resposta a outra mensagem

- **GIVEN** um evento que referencia a mensagem respondida
- **WHEN** o evento é persistido
- **THEN** o vínculo com a mensagem respondida fica disponível para o agente e a auditoria

#### Scenario: Grupo desconhecido

- **GIVEN** um evento de grupo que não é o grupo de origem nem o grupo de controle
- **WHEN** o evento é recebido
- **THEN** nenhuma resposta é enviada
- **AND** nenhum dado financeiro é alterado

### Requirement: Download de mídia

**Tipo**: Requisito funcional

O sistema SHALL baixar arquivo de imagem recebido em grupo autorizado e associá-lo à mensagem persistida. Falha de download MUST NOT ser interpretada como ausência de motorista.

#### Scenario: Imagem disponível

- **GIVEN** uma mensagem autorizada com imagem
- **WHEN** o download termina com sucesso
- **THEN** o arquivo fica associado ao identificador da mensagem e disponível para interpretação

#### Scenario: Download falha

- **GIVEN** uma imagem cujo download falha
- **WHEN** as tentativas configuradas se esgotam
- **THEN** a mensagem permanece pendente de mídia
- **AND** o administrador é informado
- **AND** nenhum motorista é marcado como não escalado

### Requirement: Envio somente a destinos autorizados

**Tipo**: Regra de negócio

O sistema SHALL enviar texto e PDF apenas ao grupo de controle, a um administrador cadastrado ou ao telefone cadastrado de um motorista quando o backend solicitar o envio. O sistema MUST NOT iniciar conversa com contato ou grupo fora dessa lista.

#### Scenario: Resumo no grupo de controle

- **GIVEN** um pedido do backend para publicar um resumo já persistido
- **WHEN** o envio é executado
- **THEN** o texto sai somente para o grupo de controle cadastrado
- **AND** o identificador da mensagem enviada fica registrado

#### Scenario: Conversa particular desconhecida

- **GIVEN** uma mensagem particular de um número que não é administrador nem motorista cadastrado
- **WHEN** o evento é recebido
- **THEN** o sistema não responde
- **AND** não envia mensagem espontânea a esse número

### Requirement: Envio de PDF

**Tipo**: Requisito funcional

O sistema SHALL enviar o PDF gerado pelo backend ao telefone cadastrado do motorista, registrar data e hora do envio e o identificador da mensagem, e informar falha sem criar lançamento financeiro.

#### Scenario: Entrega registrada

- **GIVEN** um PDF de demonstrativo e o telefone cadastrado do motorista
- **WHEN** o provedor aceita o envio
- **THEN** ficam registrados o identificador da mensagem, o instante do envio e o período do documento

#### Scenario: Telefone do motorista ausente

- **GIVEN** um PDF pronto e um motorista sem telefone cadastrado
- **WHEN** o envio é solicitado
- **THEN** o arquivo permanece armazenado
- **AND** o envio fica pendente
- **AND** o administrador é notificado
- **AND** nenhum novo valor a pagar é criado

### Requirement: Fila e retentativa

**Tipo**: Requisito não funcional

O sistema SHALL manter fila persistente de envios e repetir falha transitória com limite de tentativas. Reiniciar o processo MUST NOT apagar envio pendente nem marcar esse envio como concluído.

#### Scenario: Reinício com envio pendente

- **GIVEN** um PDF aceito na fila e ainda não confirmado pelo provedor
- **WHEN** o processo é reiniciado
- **THEN** o envio continua pendente
- **AND** uma nova tentativa não cria outro demonstrativo financeiro

#### Scenario: Limite de tentativas

- **GIVEN** um envio que falha até o limite configurado
- **WHEN** a última tentativa falha
- **THEN** o envio fica em falha
- **AND** o administrador é informado
- **AND** o sistema não continua tentando sem novo pedido

### Requirement: Reconexão e lacuna

**Tipo**: Requisito não funcional

O sistema SHALL detectar perda de conexão com a Evolution API e reconectar sem intervenção manual. Ao voltar, SHALL buscar mensagens do intervalo desconectado nos grupos autorizados quando a versão configurada da API oferecer esse recurso.

#### Scenario: Conexão restaurada com histórico

- **GIVEN** uma desconexão com mensagens recebidas no grupo de origem durante a queda
- **AND** a versão configurada da API permite recuperar esse intervalo
- **WHEN** a conexão é restabelecida
- **THEN** as mensagens ainda não armazenadas são persistidas uma única vez
- **AND** seguem o mesmo fluxo de uma mensagem recebida por webhook

#### Scenario: API sem recuperação de histórico

- **GIVEN** uma desconexão
- **AND** a versão configurada da API não oferece recuperação do intervalo
- **WHEN** a conexão volta
- **THEN** o administrador é avisado de que a lacuna não foi recuperada automaticamente
- **AND** o sistema não inventa escalas desse intervalo

### Requirement: Ordem e versão da API

**Tipo**: Requisito não funcional

O sistema SHALL aplicar cada mensagem pelo identificador do provedor, sem depender da ordem de chegada para criar duplicata. O adaptador MUST ser verificado contra a versão da Evolution API declarada na configuração e MUST NOT assumir recurso que essa versão não documenta.

#### Scenario: Evento atrasado

- **GIVEN** uma mensagem já processada
- **WHEN** um evento mais antigo do mesmo grupo chega depois
- **THEN** o evento atrasado não apaga a operação já confirmada
- **AND** não gera segunda operação para o mesmo identificador

#### Scenario: Recurso não documentado na versão

- **GIVEN** uma operação que a versão declarada da Evolution API não oferece
- **WHEN** o adaptador é preparado para essa versão
- **THEN** a ausência do recurso fica explícita para o administrador
- **AND** o sistema não simula o recurso com dado inventado

### Requirement: Destinos parametrizáveis

**Tipo**: Regra de negócio

O sistema SHALL obter grupo de origem, grupo de controle, números de administrador e telefones de motorista da configuração persistida. Esses valores MUST NOT estar escritos como condição fixa no código.

#### Scenario: Troca do grupo de controle

- **GIVEN** um administrador altera o grupo de controle na configuração
- **WHEN** o próximo resumo é publicado
- **THEN** o envio usa o novo grupo
- **AND** o grupo anterior deixa de receber mensagens do sistema

## Exceções cobertas

- Grupo desconhecido não recebe resposta nem altera financeiro.
- Conversa particular desconhecida não recebe resposta.
- Falha de download não significa motorista ausente.
- Falha ou ausência de telefone não cria lançamento financeiro.
- Lacuna não recuperável não gera escala inventada.
- Evento duplicado ou atrasado não duplica operação.
