# Etapa 4 Boas Práticas de Prompt

## Primeiro prompt:

```
Gere dados brutos para testes.
```

A LLM entendeu que deveria criar um array de objetos JSON, com um formato que ela definiu.

Além disso, criou um script auxiliar para criar os JSON, mesmo sem a minha solicitação.

## Segundo prompt:

Mais robusto e com mais regras:

```
Na pasta data/raw, quero que você crie um arquivo CSV para representar uma tabela de eventos das ações dos jogadores, para que eu possa simular uma base de dados bruta, sem ainda ter sido previamente transformada para um formato padrão. 
Mantenha em mente que precisamos simular uma POC de pipeline ETL.

Quero que o CSV tenha colunas de ID do jogador, timestamp, tipo do evento, quest ativa (ou lobby, menu. Em outras palavras, cenário do jogo), social (multiplayer, singleplayer),. Fique livre para sugerir outras características de eventos de ações dos jogadores para entendermos o comportamento deles.

Segundo a literatura, para entendermos o comportamento dos jogadores, predição de churn, engajamento, toxicidade, etc. Precisamos entender suas ações.

Quero um CSV com 1000 linhas de eventos.
```

Nesta, ela criou apenas o CSV com as regras que eu defini,
e também me fez perguntas durante a implementação para validar as decisões e sugestões.

Ela também criou novamente o script de geração do seed. Como o projeto já estava bem documentado no `README.md` e `CLAUDE.md` e a tarefa não é tão complexa (creio eu), o resultado foi até semelhante.