## Why

O escopo inicial do projeto (`docs/escopo.md`, "Objetivo inicial" do `CLAUDE.md`) prevê um worker (cronjob) que consome os eventos publicados na fila RabbitMQ, transforma-os e os persiste em um banco de dados (ETL). A primeira metade do pipeline já existe (`add-rabbitmq-publisher`, arquivada): o publisher publica continuamente, para dois jogadores de teste fixos, lotes de 15 a 20 eventos brutos em uma fila RabbitMQ única. Não há, hoje, nenhum consumidor dessa fila — as mensagens apenas se acumulam. Esta mudança implementa a segunda metade do pipeline (RabbitMQ → worker/ETL → banco), fechando o ciclo simulador → banco e preparando o terreno para o modelo de ML e a integração real do endpoint `GET /players/{player_id}/persona` (ambos fora do escopo desta change).

## What Changes

- Criar uma migração Alembic (nova revisão, após `3977097f2a32_create_users_table`) adicionando a tabela `player_features`: histórico de features agregadas por lote de eventos processado (`id` PK autoincrement, `player_id`, `session_id`, `n_events`, `pct_attack`, `pct_explore`, `pct_social`, `pct_quest_complete`, `pct_retry`, `avg_decision_time_ms`, `fail_rate`, `created_at`), com índice composto em `(player_id, id)` para consultas eficientes da linha mais recente por jogador.
- Extrair a lógica de agregação de eventos em features, hoje só em `extract_features()` (`src/player_modeling/scripts/generate_raw_events.py`), para um módulo compartilhado do worker (`src/player_modeling/worker/features.py`), sem duplicar código — mesmo padrão já usado para a geração de eventos do publisher (`simulator/events.py`). A versão compartilhada não recebe/usa persona (isso não existe nas mensagens reais da fila); o script offline de geração do dataset continua adicionando `true_persona` ao resultado, por fora, apenas para produzir `sessions_features.csv`.
- Implementar o módulo `src/player_modeling/worker/` com um subscriber que:
  - consome continuamente a fila configurada (`RABBITMQ_QUEUE`), usando `pika` (`basic_consume`, loop bloqueante) — mesmo modelo de conexão/credenciais do publisher (variáveis de ambiente obrigatórias, sem defaults hardcoded);
  - valida o formato de cada mensagem recebida (contrato fixado pela change `add-rabbitmq-publisher`: `player_id`, `session_id`, `events`); mensagens malformadas são logadas e descartadas (ack sem reprocessamento), para não travar o consumidor nem criar um loop de mensagem-veneno;
  - agrega os eventos da mensagem em uma linha de features (via `worker/features.py`) e persiste em `player_features` usando `sqlite3` puro, seguindo o padrão de `api/database.py::get_connection()`;
  - roda em primeiro plano até ser interrompido manualmente (`Ctrl+C`), espelhando o modelo de execução contínua do publisher.
- Adicionar o alvo `make subscriber` ao `Makefile` (substituindo o placeholder que já anunciava esse alvo).
- Adicionar testes automatizados em `src/tests/player_modeling/worker/`, cobrindo a extração de features, a validação/rejeição de mensagens malformadas e a persistência (usando a fixture `apply_migrations` já existente contra um SQLite de teste), mockando a conexão `pika` (sem depender de um broker real).
- Registrar as decisões (consumidor contínuo vs. cronjob one-shot; tabela única + índice composto vs. tabela de cache dual-write; schema da nova tabela; extração de `features.py`; tratamento de mensagem malformada) em uma nova ADR.

Fora de escopo desta change (ver seção "Não fazer" do `CLAUDE.md`):
- O modelo de ML de classificação Bartle (treinar/carregar um classificador) — `src/player_modeling/ml/` continua vazio.
- Qualquer alteração no endpoint `GET /players/{player_id}/persona` para consultar `player_features` ou chamar um modelo real — ele continua mockado/determinístico até o modelo existir; a integração é uma change futura separada.
- Frontend, autenticação adicional, endpoints além dos já existentes, integrações externas (PlayFab/Databricks/Redis), infraestrutura de produção/deploy.
- Qualquer alteração em `src/data/events.csv` ou `src/data/sessions_features.csv` (dados de origem, gerados apenas por `generate_raw_events.py`).

**Achado relacionado, fora do escopo desta change**: os valores atuais de `PLAYER_USERNAME_1`/`PLAYER_USERNAME_2` no `.env`/`.env.example` (`player_test_01`/`player_test_02`) não batem com o regex `^player_\d{4,}$` usado para validar `player_id`/`username` na API (`schemas.py`), o que impediria registrá-los de fato via `POST /auth/register`. Esse ajuste pertence à change do publisher (já arquivada); recomenda-se corrigi-lo separadamente (ex.: `player_9001`/`player_9002`), mas não faz parte desta proposta.

## Capabilities

### New Capabilities
- `player-feature-ingestion`: consumo contínuo da fila de eventos do jogador, agregação em features por lote e persistência em histórico no banco de dados.

### Modified Capabilities
(nenhuma — não há capability de worker/ingestão especificada em `openspec/specs/` hoje.)

## Impact

- **Banco de dados**: nova migração Alembic (`player_features` + índice composto `(player_id, id)`).
- **Código novo**: `src/player_modeling/worker/` (subscriber, extração de features).
- **Código modificado**: `src/player_modeling/scripts/generate_raw_events.py` (passa a importar a extração de features de `worker/features.py` em vez de definir localmente).
- **Testes**: nova suíte em `src/tests/player_modeling/worker/`.
- **Documentação**: nova ADR; atualização do `CLAUDE.md`/`README.md` com o comando para rodar o subscriber.
- **Makefile**: novo alvo `subscriber`, completando o par `make publisher` / `make subscriber` já anunciado.
