# Proposal

## Why

O OCR já devolve nome, código e cidades em sequência. O modelo não precisa olhar a foto. Quando o nome não está na tabela, o sistema pedia `/retry` e o endpoint manual.

## What Changes

- A foto é lida só por OCR. O modelo de visão não é chamado.
- `validaCidade` responde sim só para município do Paraná. A lista é a oficial, com 399 municípios.
- O bloco abre só na linha Douglas, quando ela não é cidade. A linha com PM1 é a rota. As cidades seguintes entram enquanto `validaCidade` responder sim. A primeira linha que não é cidade fecha o bloco.
- Cada bloco do Douglas é uma rota dele. Outro nome não gera rota. Sem Douglas, nada é gravado e nada é enviado a ele.

## Capabilities

### New Capabilities

- Nenhuma.

### Modified Capabilities

- `image-processing`: a rota sai do texto do OCR, e a cidade só entra se `validaCidade` a reconhecer.

## Impact

- Leitura da escala deixa de usar o modelo na foto.
- O pagamento continua o já definido: uma rota completa por aparição sozinha.
