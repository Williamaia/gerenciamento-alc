# Design

## Context

O corte é uma pergunta por linha. Douglas não é município, então o bloco abre. exemplo_PM1 é a rota. Congonhinhas e Nova Fátima são municípios. Nikolas não é, então o bloco fecha. Veja proposal.md.

## Goals / Non-Goals

**Goals:**

- `validaCidade` responde com a lista dos 399 municípios do Paraná.
- Gravar rota só do Douglas, percorrendo a folha toda.

**Non-Goals:**

- Não guardar uma lista de outros motoristas. Quem não é cidade só fecha o bloco.
- Não chamar o modelo de visão para a foto.
- Não mudar a tarifa já definida.

## Decisions

- A lista vem dos municípios do Paraná no IBGE. A comparação tira acento, caixa e espaços, então Nova Fatima casa com Nova Fátima.
- A linha da rota contém PM1, como exemplo_PM1. Se o OCR omitir o sublinhado, a linha continua sendo a rota.
- O bloco abre só na linha Douglas, quando `validaCidade` responde não. Outro nome não gera rota.
- Enquanto as linhas seguintes responderem sim, entram como cidades, na ordem. A primeira que responder não fecha o bloco.
- Um pedaço da cidade anterior, como Platina depois de Santo Antônio da Platina, não é outro município e não fecha o bloco.
- A palavra ambulância não é cidade e não é o motorista. Não vira rota.
- Duas linhas de nome separadas são duas rotas completas. Uma linha com ele e outra pessoa é uma rota compartilhada.
- Sem o nome, vale o caminho de não escalado. Texto vazio continua falha de leitura.

## Risks / Trade-offs

- [O OCR escrever a cidade com letra faltando] → `validaCidade` responde não e a cidade fica de fora.
- [O OCR fundir duas pessoas na mesma linha] → conta como uma rota compartilhada.

## Migration Plan

- Implantar e conferir uma escala com o nome e outra sem. O modelo não entra na foto.
- A versão anterior volta a mandar a imagem ao modelo.
