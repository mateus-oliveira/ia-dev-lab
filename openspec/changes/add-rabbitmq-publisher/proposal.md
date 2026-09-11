## Why

O escopo inicial do projeto (ver `docs/escopo.md` e "Objetivo inicial" no `CLAUDE.md`) prevê um simulador (cronjob) que gera eventos sintéticos de jogadores e os publica em uma fila RabbitMQ, para que um worker separado os consuma, transforme e persista no banco. Hoje esse simulador não existe: `src/player_modeling/simulator/__init__.py` só documenta o propósito do módulo, e os eventos sintéticos só são gerados offline, em lote, por `src/player_modeling/scripts/generate_raw_events.py`, direto para `src/data/events.csv`. Não há RabbitMQ disponível no projeto (nem `docker-compose.yml`, nem credenciais em `.env`/`.env.example`, nem cliente RabbitMQ nas dependências). Esta mudança implementa a primeira metade do pipeline (simulador → RabbitMQ), permitindo que a segunda metade (worker/ETL → banco), tratada em uma change/branch futura, tenha uma fila real para consumir.

## What Changes

- Adicionar `docker-compose.yml` na raiz subindo um container RabbitMQ (imagem `rabbitmq:3-management`, com painel web em `15672` para inspeção durante o desenvolvimento), com usuário/senha vindos de variáveis de ambiente (sem credenciais hardcoded no compose).
- Adicionar ao `.env.example` e `.env` uma nova seção com as credenciais/configuração do RabbitMQ: host, porta AMQP, usuário, senha e nome da fila, seguindo o padrão já usado para `DATABASE_PATH`/JWT no `.env.example`.
- Declarar uma única fila RabbitMQ (durável), usando o **exchange default** (routing key = nome da fila) — sem exchange customizado, adequado ao escopo de protótipo com um único produtor e um único tipo de mensagem.
- Adicionar a dependência `pika` (cliente síncrono para RabbitMQ) ao `pyproject.toml`.
- Adicionar ao `.env.example`/`.env` as variáveis `PLAYER_USERNAME_1`, `PLAYER_USERNAME_2` (os dois jogadores de teste fixos para os quais o publisher publica a cada ciclo) e `PUBLISHER_INTERVAL_SECONDS` (intervalo, em segundos, entre ciclos de publicação).
- Implementar o módulo `src/player_modeling/simulator/` com um publisher que:
  - simula um jogador com uma persona da Taxonomia de Bartle, reaproveitando a lógica de geração de eventos por persona já existente em `src/player_modeling/scripts/generate_raw_events.py` (`PERSONA_PROFILES`, `session_weights`, geração de evento único);
  - monta uma mensagem JSON com `player_id`, `session_id` (estável para o lote) e uma lista de 15 a 20 eventos recentes, no mesmo formato de linha de `src/data/events.csv` (`event_id`, `session_id`, `player_id`, `timestamp`, `event_type`, `decision_time_ms`, `outcome`);
  - publica essa mensagem na fila via `pika`.
  - **Importante**: a mensagem nunca inclui a persona/`true_persona` do jogador simulado — isso é o que o modelo de ML vai prever a partir dos eventos (worker + endpoint, fora do escopo desta change), não um dado publicado na fila.
  - **Execução contínua**: em vez de publicar uma única vez e encerrar, o publisher roda em loop — a cada ciclo, publica um lote para `PLAYER_USERNAME_1` e outro para `PLAYER_USERNAME_2` (cada um com persona sorteada independentemente), aguarda `PUBLISHER_INTERVAL_SECONDS` e repete, até ser interrompido manualmente (Ctrl+C). Isso permite observar, na prática, como o perfil previsto de um jogador de teste poderia oscilar ao longo de sucessivos ciclos de eventos, e testar isolamento de dados entre os dois jogadores conhecidos (ex.: registrados via `POST /auth/register`).
- Adicionar testes automatizados do publisher em `src/tests/player_modeling/simulator/`, cobrindo a geração de eventos, a montagem da mensagem e o ciclo de publicação para os dois jogadores configurados (mockando a conexão RabbitMQ real — os testes não devem depender de um broker ativo).
- Registrar a decisão (fila única + exchange default, formato da mensagem, `pika` síncrono, janela de 15-20 eventos, loop com intervalo configurável, jogadores de teste fixos) em uma nova ADR (`docs/adr/0007-...md`).

Fora de escopo desta change (ver seção "Não fazer" do `CLAUDE.md`):
- O worker/ETL que consome da fila, agrega os eventos em features (`sessions_features.csv`-like) e persiste no banco — será uma change/branch separada.
- O endpoint GET de perfil do jogador, o modelo de ML de classificação Bartle, frontend, autenticação/autorização adicional, integrações com PlayFab/Databricks/Redis, infraestrutura de produção ou deploy.
- Qualquer alteração em `src/data/events.csv` ou `src/data/sessions_features.csv` — esses arquivos continuam sendo gerados apenas por `generate_raw_events.py` e usados só para pré-treino.

## Capabilities

### New Capabilities
- `event-publishing`: geração de eventos sintéticos de jogador por persona e publicação em lote (15-20 eventos) em uma fila RabbitMQ, incluindo a infraestrutura local do broker (docker-compose, fila, credenciais).

### Modified Capabilities
(nenhuma — não há capability de simulador/eventos especificada em `openspec/specs/` hoje.)

## Impact

- **Código novo**: `src/player_modeling/simulator/` (publisher, geração de eventos/persona reaproveitada de `generate_raw_events.py`, montagem e publicação da mensagem).
- **Infraestrutura**: `docker-compose.yml` (raiz) com o serviço RabbitMQ.
- **Configuração**: novas variáveis no `.env.example`/`.env` (host, porta, usuário, senha, nome da fila do RabbitMQ; `PLAYER_USERNAME_1`/`PLAYER_USERNAME_2`; `PUBLISHER_INTERVAL_SECONDS`).
- **Dependências (`pyproject.toml`)**: nova dependência `pika`.
- **Testes**: nova suíte em `src/tests/player_modeling/simulator/`.
- **Documentação**: nova ADR em `docs/adr/`; atualização do `CLAUDE.md`/`README.md` com o comando para subir o RabbitMQ (`docker compose up -d`) e rodar o publisher.
- **Makefile**: novos alvos `rabbitmq-up` (sobe o RabbitMQ via docker-compose) e `publisher` (executa o worker publisher), preenchendo o placeholder já reservado para "Alvos de worker/simulador". O alvo `subscriber`, para o worker que consome da fila, será adicionado na branch/change futura desse worker.
