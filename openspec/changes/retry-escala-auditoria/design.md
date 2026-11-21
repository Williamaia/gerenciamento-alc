# Design

## Context

A leitura que falha hoje avisa o grupo de controle e não guarda a mensagem, então não há o que baixar de novo. O número conectado chega como mensagem da própria sessão e é descartado antes do comando. Veja proposal.md para o motivo.

## Goals / Non-Goals

**Goals:**

- Guardar uma única imagem de escala pendente e, no `/retry`, recomeçar o caminho dela do download até gravar.
- Levar sucesso e falha operacionais ao grupo de auditoria configurado.
- Deixar um log em cada passo. O grupo recebe o resultado, com emoticon no título.

**Non-Goals:**

- Não reler uma escala que já foi gravada.
- Não mudar parecer, pedido de paradas, quinzena nem o grupo de origem.
- Não avisar o grupo de auditoria quando o ciclo não grava nem envia nada.
- Não usar o modelo de IA para escrever log ou aviso.

## Decisions

- A pendência é um único registro: identificador da mensagem no provedor e o texto da mesma mensagem. Some na leitura confiável. Uma imagem nova sem leitura substitui a pendência anterior.
- `/retry` não tem atalho. Descarta a leitura anterior e repete o caminho de uma escala que acaba de chegar: baixa o arquivo, manda a imagem ao mesmo leitor, resolve a data pelo texto da mensagem e grava código, cidades e compartilhamento. O leitor é o modelo de visão já configurado. Não existe um OCR à parte. Paradas e quilometragem não nascem nessa hora: seguem quando o motorista responde, como em qualquer escala da madrugada. O dia que já tem paradas não é reescrito, e o grupo de controle ouve isso.
- A confirmação no grupo de controle traz só a data e os códigos. O grupo de auditoria recebe o mesmo fato como sucesso, e a falha como erro.
- O erro de auditoria tem duas frases: o que houve e um só próximo passo. Foto que não baixou, leitor que não respondeu e primeira leitura sem confiança pedem `/retry`. Data ausente, ambígua ou que pede confirmação, e a leitura que continua ruim depois do `/retry`, pedem o endpoint manual de escala e dizem que o `/retry` não resolve. Dia que já tem paradas não é reescrito por nenhum dos dois. Falha de envio não é resolvida pelo `/retry` nem por esse endpoint.
- Mensagem da própria sessão só segue quando o texto é um comando e a conversa é o grupo de controle. No grupo de origem, continua sem efeito.
- O identificador do grupo de auditoria vem da configuração, vazio por padrão. O nome Audit ALC IA não fica escrito no código. Sem esse identificador, a falha fica no log do processo.
- O log usa o registrador já existente. Entra em recebimento, leitura, comando, envio, quilometragem e agenda. A linha não leva chave, segredo, corpo cru do webhook nem a imagem. Sucesso e falha que fizeram algo também saem no grupo de auditoria. A primeira linha é o título: `✅ Frota Plus` ou `❌ Frota Plus`. A foto lida diz a data e os códigos, sem valor. O ciclo da agenda que não grava nem envia fica só no processo, para o grupo não receber aviso a cada meio minuto.
- O texto do aviso é um modelo fixo do sistema e sai pelo envio já usado na Evolution. O modelo de IA só é chamado para ler a foto da escala. Ele não redige, resume nem classifica log ou aviso. Assim o token não é gasto em auditoria.
- A resposta de `/retry` não é a linha `/retry`, para o retorno da própria sessão não disparar outra tentativa.

Alternativa descartada: buscar a última imagem no provedor a cada `/retry`. O identificador guardado na hora da falha continua válido depois que o processo reinicia, e não depende de achar a foto de novo no histórico.

## Risks / Trade-offs

- [Falha anterior a esta versão não tem identificador guardado] → `/retry` responde que não há foto, até a próxima escala que falhar.
- [O aviso de auditoria volta como mensagem da própria sessão] → o texto começa com ✅ ou ❌ e não é comando, então não gera outro envio.
- [Log demais no grupo] → o ciclo vazio não é enviado. Cada foto, comando, envio ou falha gera um aviso.

## Migration Plan

- Criar o grupo Audit ALC IA, copiar o identificador para a configuração e implantar.
- Sem essa configuração, o erro deixa de ir ao grupo de controle e fica só no processo.
- A versão anterior volta a avisar o grupo de controle e esquece a foto pendente.
