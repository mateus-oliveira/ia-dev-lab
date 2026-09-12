## 1. Banco de dados

- [x] 1.1 Criar nova migração Alembic (após `3977097f2a32_create_users_table`) criando a tabela `player_features` (`id`, `player_id`, `session_id`, `n_events`, `pct_attack`, `pct_explore`, `pct_social`, `pct_quest_complete`, `pct_retry`, `avg_decision_time_ms`, `fail_rate`, `created_at`) e o índice composto `(player_id, id)`, com `downgrade()` removendo tabela e índice. Verificar que `poetry run alembic upgrade head` aplica a migração em um banco novo e `poetry run alembic downgrade -1` reverte sem erro.
- [x] 1.2 Verificar (teste manual ou automatizado) que a migração é idempotente/consistente com a fixture `apply_migrations` já usada pelos testes da API (roda em um SQLite de teste isolado sem erro).

## 2. Extração de features compartilhada

- [x] 2.1 Criar `src/player_modeling/worker/features.py` com `extract_features(session_id, player_id, events) -> dict[str, Any]`, reaproveitando a lógica hoje em `scripts/generate_raw_events.py::extract_features` mas SEM parâmetro/campo de persona (`true_persona` não existe nas mensagens reais da fila).
- [x] 2.2 Atualizar `scripts/generate_raw_events.py` para importar `extract_features` de `worker/features.py` e adicionar `true_persona` ao dicionário retornado, por fora, ao montar `sessions_features.csv`. Verificar que regenerar o dataset com `--seed 42` continua produzindo os mesmos valores de features que o dataset atual em `src/data/` (só os UUIDs mudam, como já validado no refactor do publisher).

## 3. Worker subscriber

- [x] 3.1 Implementar em `src/player_modeling/worker/` a validação/parsing de uma mensagem consumida (checar presença e tipo de `player_id`, `session_id`, `events`), retornando o lote estruturado ou sinalizando mensagem inválida.
- [x] 3.2 Implementar a persistência de uma linha de features em `player_features` via `sqlite3` puro (seguindo o padrão de `api/database.py::get_connection()`), gerando `created_at` em Python (ISO 8601, UTC).
- [x] 3.3 Implementar o consumidor RabbitMQ contínuo (`pika`, `basic_consume`, `prefetch_count=1`, uma conexão/canal por processo): callback de mensagem parseia, agrega via `worker/features.py`, persiste, e só então confirma (`basic_ack`); mensagem malformada é logada e descartada (`basic_nack(requeue=False)`) sem interromper o consumo.
- [x] 3.4 Implementar o ponto de entrada (`python -m player_modeling.worker.subscriber`), com `channel.start_consuming()` em um `try`/`except KeyboardInterrupt` que chama `channel.stop_consuming()` e fecha a conexão de forma limpa.
- [x] 3.5 Adicionar ao Makefile o alvo subscriber (substituindo o placeholder existente), documentado no help, e verificar manualmente (RabbitMQ + publisher rodando) que make subscriber consome as mensagens publicadas e grava linhas em player_features (conferir via sqlite3 db.sqlite3 "select * from player_features" ou equivalente).

## 4. Testes

- [x] 4.1 Criar `src/tests/player_modeling/worker/test_features.py` cobrindo `extract_features` (proporções corretas, ausência de qualquer campo de persona) e verificar que `poetry run pytest src/tests/player_modeling/worker/test_features.py` passa.
- [x] 4.2 Criar testes cobrindo parsing/validação de mensagem (válida e malformada), persistência real em `player_features` usando a fixture `apply_migrations` contra um SQLite de teste, e o fluxo de consumo mockando a conexão `pika` (sem broker real) — incluindo o caso de mensagem malformada resultando em `basic_nack(requeue=False)` e mensagem válida resultando em `basic_ack` após persistir. Implementado como `test_messages.py`, `test_repository.py` e `test_subscriber.py` (um arquivo por módulo, seguindo a convenção de testes do `CLAUDE.md`, em vez de um único `test_subscriber.py`). Verificado que `poetry run pytest src/tests/player_modeling/worker/` passa (15 testes).
- [x] 4.3 Rodar `poetry run pytest` (suíte completa), `poetry run ruff check .`, `poetry run ruff format --check .` e `poetry run mypy .`, e verificar que tudo passa sem regressões nos testes/harness existentes (incluindo os testes já existentes que dependem da migração de `users`).

## 5. Documentação

- [x] 5.1 Criar `docs/adr/0008-worker-subscriber-features.md` documentando as decisões de `design.md` (consumidor contínuo, tabela única + índice composto, extração de `features.py` sem persona, tratamento de mensagem malformada, ack somente após persistir).
- [x] 5.2 Atualizar `CLAUDE.md` (seção "Comandos") e `README.md` com o comando para rodar o subscriber (`make subscriber`) e uma breve descrição do que ele persiste, e verificar que os comandos documentados funcionam como descrito.
