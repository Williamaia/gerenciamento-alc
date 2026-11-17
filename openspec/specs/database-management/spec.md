# Gestão de dados

## Purpose

Persistir cadastros, operação, financeiro, mensagens e documentos em PostgreSQL, com decimal, unicidade, integridade e transação, de modo que reinício não perca fato confirmado.

## Objetivo

O banco é a fonte oficial. Esta spec define o que precisa ser guardado e quais combinações não podem duplicar. Ela não escolhe framework nem escreve SQL de implementação.

## Dependências

- Todas as specs de negócio dependem destes invariantes.
- `security-and-permissions`: configuração sem segredo no código e acesso a documentos.
- `audit-and-history`: histórico ligado aos registros oficiais.
- `task-scheduling`: fila e agendamento sobrevivem a reinício.

## Requirements

### Requirement: Banco oficial

**Tipo**: Requisito não funcional

O sistema SHALL usar PostgreSQL como única fonte oficial dos dados operacionais e financeiros. A memória do agente, arquivo temporário ou mensagem de WhatsApp MUST NOT substituir o registro confirmado.

#### Scenario: Consulta depois de reinício

- **GIVEN** uma operação confirmada antes do desligamento
- **WHEN** o processo volta e a operação é consultada
- **THEN** o estado confirmado é o que estava no PostgreSQL
- **AND** não depende da memória de uma conversa anterior

### Requirement: Cadastros persistidos

**Tipo**: Requisito funcional

O sistema SHALL persistir motoristas, veículos, grupos autorizados, administradores, rotas, cidades, trevos, distâncias entre trevos e configurações operacionais, com os relacionamentos necessários para executar as regras das specs correspondentes.

#### Scenario: Distância recuperável

- **GIVEN** uma distância cadastrada entre dois trevos
- **WHEN** uma operação posterior usa o mesmo sentido
- **THEN** a distância é lida do banco
- **AND** não precisa ser informada de novo

### Requirement: Operação persistida

**Tipo**: Requisito funcional

O sistema SHALL persistir escala interpretada, operação diária, rotas executadas, cidades observadas, paradas, quilometragem e o estado de cada uma. A operação diária SHALL identificar data, motorista e veículo.

#### Scenario: Operação com rota observada

- **GIVEN** uma escala confirmada com código ainda não cadastrado
- **WHEN** ela é gravada
- **THEN** a execução conserva o código e as cidades observadas
- **AND** a pendência de quilometragem permanece consultável

### Requirement: Financeiro persistido

**Tipo**: Requisito funcional

O sistema SHALL persistir linhas de pagamento, valor unitário, total, indicador de paradas, fechamento, versão, documento PDF e situação de envio. Pagamento e indicador de paradas SHALL ocupar fatos separados.

#### Scenario: Dois fatos do mesmo dia

- **GIVEN** um dia com pagamento de motorista e indicador de paradas
- **WHEN** os dados são gravados
- **THEN** é possível ler cada valor sem derivar um do outro
- **AND** apagar ou corrigir o indicador não reescreve sozinho o pagamento

### Requirement: Mensagens persistidas

**Tipo**: Requisito funcional

O sistema SHALL persistir mensagens recebidas e enviadas, com identificador do provedor, grupo ou destino, remetente, vínculo de resposta quando houver, instante, resultado e referência da mídia ou do documento.

#### Scenario: Envio rastreável

- **GIVEN** um PDF enviado com sucesso
- **WHEN** a auditoria consulta a entrega
- **THEN** encontra identificador da mensagem, instante e versão do documento

### Requirement: Tipo monetário e decimal

**Tipo**: Requisito não funcional

Valores monetários e distâncias SHALL usar tipo decimal do PostgreSQL, nunca ponto flutuante. Dinheiro SHALL ter escala suficiente para centavos. O sistema MUST NOT gravar valor monetário como aproximação binária.

#### Scenario: Valor de uma rota

- **GIVEN** a tarifa de R$ 100,00
- **WHEN** ela é persistida e lida
- **THEN** o valor retornado é exatamente R$ 100,00

#### Scenario: Indicador com centavos

- **GIVEN** o indicador confirmado de R$ 82,50
- **WHEN** ele é persistido e lido
- **THEN** o valor retornado é exatamente R$ 82,50

### Requirement: Unicidade

**Tipo**: Regra de negócio

O sistema SHALL impedir mais de uma mensagem recebida com o mesmo identificador do provedor, mais de uma operação por data, motorista e veículo, mais de uma versão de fechamento para o mesmo motorista e período, e mais de uma distância para o mesmo par de trevos no mesmo sentido.

#### Scenario: Segunda gravação da mesma operação

- **GIVEN** uma operação já gravada para data, motorista e veículo
- **WHEN** outro fluxo tenta criar outra operação dessa mesma chave
- **THEN** o banco recusa a duplicata
- **AND** a operação original continua sendo a única

### Requirement: Integridade

**Tipo**: Requisito não funcional

O sistema SHALL manter integridade referencial entre operação, motorista, veículo, linhas de pagamento, fechamento e documento. Exclusão física MUST NOT apagar histórico financeiro confirmado; inativação SHALL conservar os vínculos já usados.

#### Scenario: Motorista com pagamento

- **GIVEN** um motorista com operação confirmada
- **WHEN** ele é inativado
- **THEN** a operação antiga continua ligada a ele
- **AND** o registro financeiro não é removido

### Requirement: Transação financeira

**Tipo**: Requisito não funcional

Confirmação, ajuste e consolidação SHALL ocorrer em uma transação. Qualquer falha SHALL desfazer todas as escritas daquela transação.

#### Scenario: Erro no meio da consolidação

- **GIVEN** um fechamento que falha depois de gravar parte dos dados e antes de concluir
- **WHEN** a transação termina com erro
- **THEN** não permanece fechamento parcial
- **AND** as operações do período continuam no estado anterior

### Requirement: Consultas operacionais

**Tipo**: Requisito não funcional

O sistema SHALL manter índices adequados para localizar mensagem pelo identificador do provedor, operação por data e motorista, fechamento por período e distância por par de trevos, de modo que a consulta de quinzena e a deduplicação não dependam de varredura desnecessária.

#### Scenario: Deduplicação por identificador

- **GIVEN** um identificador de mensagem já armazenado
- **WHEN** o mesmo identificador chega
- **THEN** a existência anterior é encontrada pela chave única
- **AND** nenhuma segunda linha é gravada

### Requirement: Backup do PostgreSQL

**Tipo**: Requisito não funcional

O sistema SHALL gerar ao menos um backup lógico diário do PostgreSQL, em destino configurável e fora do acesso público, com retenção configurável. A retenção inicial SHALL ser de 30 dias quando não houver outro valor. Falha de backup SHALL avisar o administrador. Restauração MUST NOT ocorrer sem ação administrativa explícita.

#### Scenario: Backup diário concluído

- **GIVEN** o destino de backup configurado
- **WHEN** a janela diária de backup termina com sucesso
- **THEN** existe um dump lógico restaurável em PostgreSQL
- **AND** backups mais antigos que a retenção são removidos

#### Scenario: Falha de backup

- **GIVEN** o destino de backup indisponível
- **WHEN** a tentativa do dia falha
- **THEN** o administrador é avisado
- **AND** os dados oficiais não são alterados para compensar a falha

## Exceções cobertas

- Duplicata de mensagem, operação, versão ou distância é recusada.
- Falha de transação não deixa fechamento parcial.
- Inativação não apaga histórico.
- Ponto flutuante não representa dinheiro nem distância oficial.
- Falha de backup não altera dado oficial e não restaura nada sozinha.
