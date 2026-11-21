# Spec Delta

## ADDED Requirements

### Requirement: Foto pendente para nova tentativa

**Tipo**: Exceção

Quando a imagem de escala não for lida com confiança, ou o arquivo não vier, o sistema SHALL guardar o identificador da mensagem do provedor para uma nova tentativa. MUST NOT gravar motorista, código, cidade ou pagamento a partir dessa falha. O aviso SHALL ir ao grupo de auditoria, com título começando em ❌, e MUST NOT ir ao grupo de controle.

#### Scenario: Leitura sem confiança

- **GIVEN** uma imagem de escala no grupo de origem
- **WHEN** a leitura termina sem confiança
- **THEN** o identificador da mensagem fica guardado
- **AND** nenhuma rota é gravada
- **AND** o grupo de auditoria recebe o aviso com título começando em ❌
- **AND** o grupo de controle não recebe esse aviso
- **AND** nenhum motorista é marcado como não escalado

#### Scenario: Arquivo ausente

- **GIVEN** uma imagem de escala cujo arquivo não pôde ser baixado
- **WHEN** a tentativa termina
- **THEN** o identificador da mensagem fica guardado
- **AND** a mensagem continua pendente de mídia
- **AND** nenhum palpite de rota é gravado
