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
19. O grupo de origem, só para leitura das escalas, é ALC SANTO ANTÔNIO DA PLATINA EPR7 MOTORISTAS. Nenhuma mensagem é enviada para ele.
20. O relatório diário sai no grupo Gerenciamento ALC IA.
21. O WhatsApp do Douglas é 55 65 9960-7901. Esse mesmo número recebe o faturamento no dia 15 e no último dia do mês, e também o pedido diário de paradas.
22. O ganho diário da Fiorino segue a tabela de frete do utilitário em Santo Antônio da Platina, guardada em `docs/referencias/tabela-frete-utilitario.png`. A faixa usa a quilometragem de ida e volta: até 100 km, R$ 235,00; 101 a 150, R$ 260,00; 151 a 200, R$ 305,00; 201 a 250, R$ 335,00; 251 a 300, R$ 355,00; acima de 300, R$ 380,00. A bonificação por parada é progressiva: R$ 0,35 até a 60ª, R$ 1,90 da 61ª à 90ª e R$ 0,90 da 91ª em diante. Duas ou mais encomendas no mesmo lugar contam como uma parada, e só entra parada entregue. O bônus de treinamento é R$ 5,00 por rota somente com aderência concluída de pelo menos 95%. Esse ganho não se soma ao pagamento do motorista.
23. O combustível padrão é R$ 90,00 por dia. O lucro do dia é o ganho da Fiorino menos o pagamento do motorista, o combustível e as manutenções. Para mudar o combustível de um dia: `/ajustar combustivel=80 data=17/11`. Sem data, o comando vale para a operação já resolvida.
24. A data da escala é a data escrita no texto que acompanha a imagem. A frase ao redor pode mudar. "Segue a escala 17/11" é só um exemplo, não um texto obrigatório.
25. Manutenção: `/manutencao "Troca de Óleo" 200,00`. Com parecer já publicado, a mensagem do grupo é editada. Em dia sem rota, o grupo de controle recebe somente a manutenção. No fechamento, o grupo de controle recebe o relatório da quinzena da Fiorino, com cada dia, a soma dos ganhos, os pagamentos do motorista já líquidos de PNR, abastecimentos, manutenções e lucro.
26. O demonstrativo do Douglas lista cada dia da quinzena e a soma. Dia sem rota aparece com valor zero. PNR é pacote perdido ou entregue errado. O administrador só fica sabendo quando recebe o faturamento da ALC e então envia `/pnr 30,00` no grupo de controle. O desconto vale para a quinzena desse faturamento. O valor de cada rota não muda. Se a quinzena já estiver fechada, sai uma versão nova e a anterior não é somada.
27. Às 08:00 o frota-plus-agent pede as paradas ao Douglas e só guarda a resposta. Não responde mais nada nessa conversa. O parecer sai no grupo de controle. O demonstrativo da quinzena continua sendo enviado no dia 15 e no último dia.
28. A quilometragem de cada cidade é a ida e a volta a partir de Santo Antônio da Platina, consultadas separadas. Congonhinhas fica em 73 km e 73 km. Cidade nova é buscada na hora e guardada. Várias cidades na rota, ou em rotas do mesmo dia, somam cidade por cidade. Se faltar a distância de uma cidade, o dia inteiro fica pendente.

## Pendências que não impedem a spec

Não estão no repositório e não devem ser inventadas:

- Número do administrador.
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
