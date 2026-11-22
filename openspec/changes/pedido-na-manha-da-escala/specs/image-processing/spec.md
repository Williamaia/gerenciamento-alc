# Spec Delta

## ADDED Requirements

### Requirement: Rota de outro motorista

**Tipo**: Regra de negócio

O sistema SHALL gravar rota para o motorista monitorado somente quando a leitura encontrar o nome dele na célula de motorista. Sem esse nome, SHALL ficar sem rota e MUST NOT enviar mensagem a ele. MUST NOT tratar essa leitura como foto ilegível nem como pedido de nova tentativa.

#### Scenario: Escala sem o motorista

- **GIVEN** a escala de 22/11 recebida em 21/11 às 23:09
- **AND** a leitura não encontra o nome Douglas
- **AND** B25_PM1 é rota de outra pessoa
- **WHEN** a leitura termina
- **THEN** B25_PM1 não fica gravada para ele
- **AND** nenhuma mensagem é enviada a ele
- **AND** a leitura não é tratada como foto ilegível

#### Scenario: Nome na célula da rota

- **GIVEN** o nome do motorista monitorado está na célula de motorista de uma rota
- **WHEN** a leitura dessa rota termina com confiança
- **THEN** essa rota fica gravada para ele
