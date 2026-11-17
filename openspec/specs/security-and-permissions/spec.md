# Segurança e permissões

## Purpose

Garantir que somente administradores autorizados alterem dados, que webhooks e segredos sejam verificáveis e que documentos, logs e falhas de integração não exponham ou dupliquem informação.

## Objetivo

A autorização é por número e grupo cadastrados. Credencial fica em ambiente ou cofre de configuração, nunca no código. Mensagem não autorizada não muda financeiro. Documento e log seguem o mesmo limite.

## Dependências

- `whatsapp-integration`: aplica a verificação do webhook e o destino do envio.
- `whatsapp-commands` e `ai-agent`: só continuam depois da autorização.
- `financial-reports`: acesso ao PDF.
- `database-management`: configuração e unicidade.
- `audit-and-history`: registra tentativa e alteração.

## Requirements

### Requirement: Administradores

**Tipo**: Regra de negócio

O sistema SHALL reconhecer administrador por número cadastrado. Somente esse remetente, no canal permitido, SHALL alterar cadastro, operação, pagamento, fechamento ou configuração. A lista SHALL ser parametrizável.

#### Scenario: Número cadastrado

- **GIVEN** um número presente na lista de administradores
- **WHEN** ele envia um comando no canal permitido
- **THEN** a autorização de administrador é concedida

#### Scenario: Número parecido não cadastrado

- **GIVEN** um número que apenas se parece com o do administrador
- **WHEN** ele pede alteração financeira
- **THEN** a alteração é recusada
- **AND** o registro oficial permanece

### Requirement: Grupos e motorista

**Tipo**: Regra de negócio

O sistema SHALL tratar apenas os grupos cadastrados como origem ou controle. O motorista SHALL poder receber o próprio demonstrativo e MUST NOT alterar dado financeiro, mesmo que escreva um comando válido.

#### Scenario: Comando válido de quem não é administrador

- **GIVEN** qualquer remetente não administrador envia "/ajustar douglas rotas=0"
- **WHEN** a autorização é avaliada
- **THEN** o comando não é aplicado
- **AND** nenhuma resposta revela dados financeiros de terceiros

### Requirement: Webhook autêntico

**Tipo**: Requisito não funcional

O sistema SHALL verificar a autenticidade de cada webhook pelo mecanismo da versão configurada da Evolution API. Evento que falhe nessa verificação MUST NOT gerar mensagem, fila, interpretação ou alteração.

#### Scenario: Assinatura ou credencial inválida

- **GIVEN** uma requisição de webhook que não satisfaz a verificação configurada
- **WHEN** ela chega
- **THEN** não há efeito operacional
- **AND** a credencial esperada não é escrita no log

### Requirement: Segredos

**Tipo**: Requisito não funcional

Token, senha, chave de API e segredo de webhook SHALL existir somente em variável de ambiente ou mecanismo equivalente fora do código. O sistema MUST NOT gravar esses segredos no repositório, na spec executável, no log ou na resposta de WhatsApp.

#### Scenario: Inicialização sem segredo

- **GIVEN** a configuração obrigatória de integração está vazia
- **WHEN** o processo inicia
- **THEN** a integração não é tratada como conectada
- **AND** o sistema não usa segredo padrão embutido

### Requirement: Logs

**Tipo**: Requisito não funcional

O sistema SHALL emitir log estruturado com identificador de correlação, evento, resultado e instante. Log MUST NOT incluir segredo, conteúdo integral de credencial ou PDF.

#### Scenario: Falha de envio

- **GIVEN** uma falha ao enviar mensagem
- **WHEN** a falha é registrada
- **THEN** o log permite identificar a mensagem e o resultado
- **AND** não contém a chave da API

### Requirement: Documentos

**Tipo**: Requisito não funcional

PDF e imagem de escala SHALL ficar fora de acesso público. O sistema SHALL entregá-los apenas pelo envio autorizado ou por pedido de reenvio de administrador. MUST NOT publicar URL aberta permanente.

#### Scenario: Tentativa de acesso direto

- **GIVEN** um demonstrativo armazenado
- **WHEN** não há envio autorizado nem reenvio de administrador
- **THEN** o arquivo não é disponibilizado publicamente

### Requirement: Duplicidade e tentativas

**Tipo**: Requisito não funcional

O sistema SHALL rejeitar efeito duplicado de mensagem já processada e SHALL limitar tentativas de envio e de download. Esgotar a tentativa SHALL registrar falha e avisar o administrador, sem repetição infinita.

#### Scenario: Replay de mensagem

- **GIVEN** uma mensagem já processada
- **WHEN** o mesmo identificador é apresentado outra vez
- **THEN** não há nova alteração financeira
- **AND** não há novo envio de resumo

### Requirement: Falha da integração

**Tipo**: Exceção

Falha da Evolution API MUST NOT ser compensada com alteração financeira local inventada. O sistema SHALL conservar a fila, registrar a falha e permitir nova tentativa dentro do limite.

#### Scenario: Provedor indisponível no fechamento

- **GIVEN** um PDF consolidado e o provedor indisponível
- **WHEN** o envio falha
- **THEN** a consolidação não é desfeita
- **AND** o envio permanece pendente ou em falha, conforme o limite
- **AND** nenhum segundo total é criado

## Exceções cobertas

- Remetente não autorizado não altera financeiro.
- Webhook inválido não tem efeito.
- Segredo ausente não é substituído por padrão.
- Replay não duplica efeito.
- Falha do provedor não inventa lançamento nem desfaz consolidação já feita.
