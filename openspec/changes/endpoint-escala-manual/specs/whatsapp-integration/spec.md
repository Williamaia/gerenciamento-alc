# Spec Delta

## MODIFIED Requirements

### Requirement: Reconexão e lacuna

**Tipo**: Requisito não funcional

O sistema SHALL detectar perda de conexão com a Evolution API e reconectar sem intervenção manual. Ao voltar, SHALL buscar mensagens do intervalo desconectado nos grupos autorizados quando a versão configurada da API oferecer esse recurso. Sem essa recuperação, a escala faltante SHALL entrar pelo endpoint de escala manual. O sistema MUST NOT inventar o que não foi informado.

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
- **AND** a escala faltante pode ser registrada no endpoint de escala manual
