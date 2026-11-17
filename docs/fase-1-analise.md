# Fase 1 — Análise e relatório das specs

Estado: especificações propostas, aguardando aprovação. Nenhum código do Frota Plus foi implementado. Nenhuma change foi aberta.

## Ferramenta

- Workspace vazio no início. O comando `openspec` não estava instalado.
- Node.js usado: v26.3.0.
- OpenSpec instalado no projeto: `@fission-ai/openspec` 2.1.0.
- Inicialização real: `openspec init --tools cursor --scope project --language "português do Brasil" --profile core`.
- Schema: `spec-driven`.
- Nesta versão, as skills do Cursor ficam em `.agents/skills/`. O init não cria `.cursor/`.
- Validação: `npx openspec validate --specs --strict --no-interactive` — 15 specs aprovadas, 127 requisitos.

O diretório do produto é a raiz deste workspace. O nome do pacote é `frota-plus`. Não foi criada uma pasta interna com o mesmo nome, para o OpenSpec ficar na raiz que o CLI reconhece.

## Specs criadas

| Spec | Requisitos | Cobre |
|---|---|---|
| `whatsapp-integration` | 9 | Evolution API, webhook, mídia, envio, fila, reconexão |
| `ai-agent` | 8 | Interpretação, separação do backend, memória oficial |
| `image-processing` | 12 | Data da mensagem, tabela, layout variável, ausência, imagens de referência e recusa de palpite quando a foto está ruim |
| `driver-management` | 6 | Cadastro, Douglas inicial, grafias, tarifas |
| `vehicle-management` | 5 | Frota extensível e Fiorino de referência |
| `route-management` | 7 | Rotas, cidades, trevos, códigos como dados |
| `mileage-calculation` | 7 | Trevo a trevo, pendência e ajuste manual |
| `stops-calculation` | 6 | Faixas progressivas e separação do pagamento |
| `driver-payments` | 12 | Completa, compartilhada, ausência, ajuste |
| `financial-reports` | 12 | Resumo, PDF, quinzena, versão e reenvio |
| `whatsapp-commands` | 9 | Comandos, frases e autorização |
| `security-and-permissions` | 8 | Número, grupo, webhook, segredo, documento |
| `database-management` | 11 | PostgreSQL, decimal, unicidade, backup |
| `audit-and-history` | 7 | Trilha imutável e versões |
| `task-scheduling` | 8 | 17:00, recuperação, trava, observação |

## Cobertura dos requisitos

- WhatsApp por webhook, com grupo, remetente, resposta, mídia, texto, PDF, duplicata, falha e reconexão.
- Agente que pede ação e backend que calcula. PostgreSQL é a fonte oficial.
- Data explícita da mensagem, nunca a data de recebimento quando a mensagem traz dia e mês.
- Leitura de motorista, rota, cidade e parada, inclusive cidade em linha seguinte.
- Ausência de Douglas só com escala completa e confiável. Dúvida fica aguardando confirmação.
- Douglas inicial: R$ 100,00 completa e R$ 50,00 compartilhada, valores editáveis e fora do código.
- Rotas, cidades, trevos e distâncias cadastráveis. Código de rota não fica fixo.
- Quilometragem = ida + trechos + retorno. Trecho faltante não vira número.
- Paradas: 60 × 0,35, depois 30 × 1,90, depois 0,90. O exemplo de 95 paradas resulta em R$ 82,50.
- Esse indicador não entra no pagamento nem no PDF.
- Resumo no grupo de controle e demonstrativo só do motorista.
- Fechamentos de 1–15 e de 16–último dia, às 17:00, `America/Sao_Paulo`.
- Idempotência, versão revisada e reenvio sem novo lançamento.
- Comandos iniciais e as três frases naturais citadas no pedido.
- Auditoria, transação, decimal, fila persistente, backup diário e estado operacional.

## Dependências

```text
security-and-permissions
database-management
audit-and-history
        │
        ├── driver-management ── vehicle-management
        ├── route-management ─── mileage-calculation
        ├── stops-calculation
        └── whatsapp-integration
                 │
                 ├── image-processing
                 ├── ai-agent
                 └── whatsapp-commands
                          │
                          ├── driver-payments
                          └── financial-reports
                                   │
                                   └── task-scheduling
```

A ordem de implementação sugerida para a Fase 2, ainda sem abrir changes:

1. Banco, segurança e auditoria.
2. Motoristas, veículos e rotas.
3. Quilometragem e paradas, com testes de soma e faixas.
4. Pagamento do motorista.
5. Integração WhatsApp.
6. Imagem e agente.
7. Comandos.
8. Relatório, PDF e agendamento.

## Decisões já escritas nas specs

A aprovação destas specs confirma as decisões abaixo.

1. Dia sem nenhuma mensagem não vira "não escalado" e não bloqueia a quinzena. O administrador é avisado. Imagem recebida e ainda não confirmada bloqueia.
2. Data sem ano usa o ano do recebimento em `America/Sao_Paulo`. Se o resultado ficar mais de sete dias no futuro, pede confirmação.
3. O pagamento multiplica pelo número de vezes que o nome do motorista aparece. Várias cidades na mesma aparição contam como uma rota só.
4. Três ou mais pessoas na mesma rota geram uma única compartilhada, sem tarifa nova.
5. O mesmo código repetido no dia não paga duas vezes sem confirmação.
6. Completa e compartilhada no mesmo dia se somam.
7. Código de rota desconhecido não bloqueia o pagamento já confirmado pela modalidade. A quilometragem fica pendente.
8. Cidade divergente não reescreve o cadastro da rota nem confirma quilometragem.
9. Distância de volta não é copiada da ida. Zero cadastrado é zero; ausência não é zero.
10. Quilometragem manual não altera a tabela nem o pagamento.
11. A tarifa é copiada para a operação na confirmação. Ajuste de quantidade reutiliza essa cópia.
12. Correção depois do fechamento cria outra versão, conserva a anterior, envia o PDF novo ao motorista e não soma as versões.
13. Comando administrativo vale na conversa particular do administrador ou no grupo de controle. Não vale no grupo da ALC. Douglas recebe PDF e não altera financeiro.
14. `/fechar quinzena` pode rodar antes das 17:00 e fica marcado como manual. O relógio automático só dispara no dia 15 e no último dia.
15. Não há painel web nesta versão.
16. O aviso de dias sem escala lista os dias corridos do período, inclusive fim de semana.
17. Backup lógico diário, retenção inicial de 30 dias, sem restauração automática.
18. `/ajustar rotas=0` zera rotas completas. Se não restar compartilhada, o dia fica não escalado.

## Pendências que não impedem a spec

Não estão no repositório e não devem ser inventadas:

- Números do administrador e do Douglas.
- Identificadores dos grupos de origem e de controle.
- Identificação da primeira Fiorino e do ponto exato do barracão.
- Tabela inicial de trevos e distâncias.
- URL, instância e versão da Evolution API que será usada.
- Provedor e modelo de IA.

Esses itens entram por configuração na implantação.

## Referências visuais

As três escalas estão em `docs/referencias/`.

| Arquivo | O que a imagem mostra sobre o Douglas | Pagamento informado |
|---|---|---|
| `escala-01-uma-rota.png` | Sozinho em D9_PM1, Congonhinhas | R$ 100,00 |
| `escala-02-duas-rotas.png` | Sozinho em C25_PM1 e B15_PM1, Nova Fátima | R$ 200,00 |
| `escala-03-rota-dividida.png` | Douglas sozinho em A27_PM1 (Santa Amélia, Ribeirão do Pinhal, Nova Fátima e Congonhinhas) e "Wesley e Douglas" em B14_PM1 (Ribeirão do Pinhal e Trolândia) | R$ 100,00 + R$ 50,00 = R$ 150,00 |

Várias cidades na mesma aparição do nome contam como uma rota. O pagamento só multiplica quando o nome do Douglas aparece mais de uma vez. Na terceira imagem, o nome aparece duas vezes: A27_PM1 a R$ 100,00 e B14_PM1 a R$ 50,00. A linha final, Everson / ambulância / região de Andirá, não é rota.

## Ambiguidades tratadas

- "Não recebida" foi lido como diferente de "recebida e ainda não interpretada". Só o segundo caso bloqueia o fechamento.
- O exemplo de uma e duas rotas foi generalizado para N rotas, porque a regra é por rota e não um teto de duas.
- O indicador de paradas é exibido no controle e não é pago a ninguém nesta versão.
- A autenticação do administrador é o número de WhatsApp cadastrado. Não foi especificada senha de painel.

## Sugestões para depois da aprovação

- Calendário opcional de dias em que se espera escala, para o aviso quinzenal não tratar domingo como esquecimento.
- Escolher o provedor de visão na change do agente, comparando a qualidade da tabela com as três imagens de referência.
- Deixar tarifa por veículo e novos motoristas monitorados para changes próprias. O cadastro já permite o registro.

## Fora desta fase

Não foram criados código em `src/`, testes executáveis, changes, proposals, tasks de implementação nem archive de change. `package.json` existe apenas para fixar o OpenSpec 2.1.0.
