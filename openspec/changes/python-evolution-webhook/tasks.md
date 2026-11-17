# Tasks

## 1. Serviço

- [x] 1.1 Criar o pacote Python com configuração por ambiente e o caminho `POST /webhooks/evolution`. Verificar com `pytest`.
- [x] 1.2 Expor `GET /health` com a URL do webhook, sem segredo. Verificar que a resposta não contém a chave do agente.
- [x] 1.3 Recusar webhook sem segredo configurado e com segredo errado. Verificar os códigos 503 e 401.
- [x] 1.4 Aceitar evento autêntico, ignorar duplicata pelo identificador e não devolver pagamento nem `apikey`. Verificar com dois envios do mesmo `data.key.id`.

## 2. Operação local

- [x] 2.1 Guardar a chave do agente somente no `.env`, ignorado pelo Git. Verificar que `.gitignore` contém `.env` e que o exemplo versionado não tem segredo.
- [x] 2.2 Documentar a URL que será cadastrada na Evolution. Verificar o endereço no README.
