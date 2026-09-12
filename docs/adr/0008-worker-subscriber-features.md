# ADR 0008 - Worker subscriber e tabela `player_features`

* **Status:** Aceito
* **Data:** 2026-09-11
* **Decisão:** Implementação do worker subscriber (`src/player_modeling/worker/`), consumidor contínuo da fila RabbitMQ que agrega cada lote de eventos em uma linha de features e a persiste em uma tabela de histórico única (`player_features`), fechando o ciclo simulador → RabbitMQ → worker → banco.

## Contexto

A [ADR 0007](0007-simulador-publisher-rabbitmq.md) implementou a primeira metade do pipeline (publisher): eventos sintéticos de dois jogadores de teste fixos são publicados continuamente em uma fila RabbitMQ única, no formato `{"player_id": str, "session_id": str, "events": [...]}`. Até esta decisão, nada consumia essa fila — as mensagens apenas se acumulavam. Esta ADR cobre a segunda metade do pipeline: o worker/ETL que consome, agrega e persiste.

O acesso a dados em runtime no projeto é `sqlite3` puro (não SQLAlchemy Core/ORM), com schema gerenciado por Alembic (ADR 0006) via migrações escritas manualmente. O endpoint `GET /players/{player_id}/persona` já existe como stub/mock (change `inference-endpoint`, arquivada) e continua mockado nesta mudança — a integração com dados reais depende também do modelo de ML (`src/player_modeling/ml/`, ainda vazio), fora do escopo aqui.

## Decisões

### 1. Consumidor contínuo, não cronjob one-shot
O subscriber consome a fila continuamente (`pika`, `basic_consume`, loop bloqueante via `channel.start_consuming()`), processando mensagens assim que chegam, em vez de rodar uma vez, drenar o que estiver disponível e encerrar. Decisão tomada diretamente com o desenvolvedor: espelha o publisher (ADR 0007, decisão 8), que também roda continuamente, e evita a necessidade de agendamento externo (cron do SO) para observar o pipeline funcionando de ponta a ponta em tempo real durante o desenvolvimento. Alternativa considerada (cronjob one-shot, mais fiel ao termo usado em `docs/escopo.md`): descartada por exigir infraestrutura de agendamento externa que não agrega valor neste protótipo local.

### 2. Tabela única de histórico (`player_features`) com índice composto `(player_id, id)`
Decisão tomada diretamente com o desenvolvedor, após análise de trade-off. Cada mensagem processada vira uma nova linha em `player_features` (1 jogador : N linhas), preservando auditoria completa. Para consultar eficientemente a linha mais recente de um jogador (uso futuro do endpoint), um índice composto em `(player_id, id)` permite ao SQLite localizar as linhas do jogador e escolher o maior `id` sem varrer a tabela inteira. Usa-se `id` (autoincrement, proxy monotônico da ordem de inserção) em vez de `created_at` para "mais recente", evitando problemas de colisão/precisão de timestamp.

**Alternativa descartada**: uma segunda tabela `player_latest_features` (1:1 com o jogador, sobrescrita a cada mensagem) para tornar a busca O(1). Rejeitada por introduzir *dual-write* — toda inserção no histórico exigiria um upsert sincronizado na tabela "latest", na mesma transação — para um ganho de performance irrelevante na escala deste protótipo (dezenas de milhares de linhas mesmo após meses de execução contínua com dois jogadores).

**Alternativa possível no futuro, não implementada agora**: uma `VIEW` SQL computando a linha mais recente por jogador sob demanda, sem duplicar dados — só valeria a pena se essa consulta passasse a ser usada em vários lugares.

`player_features.player_id` não tem `FOREIGN KEY` para `users.username`: o worker persiste features de qualquer `player_id` recebido na fila, independente de cadastro via `/auth/register`.

### 3. Schema da tabela

| Coluna | Tipo | Observação |
| --- | --- | --- |
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | |
| `player_id` | `VARCHAR(100) NOT NULL` | |
| `session_id` | `VARCHAR(36) NOT NULL` | |
| `n_events` | `INTEGER NOT NULL` | |
| `pct_attack`, `pct_explore`, `pct_social`, `pct_quest_complete`, `pct_retry`, `fail_rate` | `FLOAT NOT NULL` | |
| `avg_decision_time_ms` | `FLOAT NOT NULL` | |
| `created_at` | `VARCHAR(32) NOT NULL` | ISO 8601 UTC, gerado em Python no momento da persistência |

Índice: `ix_player_features_player_id_id` em `(player_id, id)`.

### 4. Extração de `extract_features()` para `worker/features.py`, sem persona
A lógica de agregação (antes só em `scripts/generate_raw_events.py::extract_features`) foi extraída para `worker/features.py`, com uma mudança de assinatura: a versão compartilhada não recebe nem retorna `persona`/`true_persona` — esse rótulo não existe nas mensagens reais da fila, só no dataset de treino gerado offline. `generate_raw_events.py` passa a chamar a versão compartilhada e adicionar `true_persona` ao resultado, por fora, só para compor `sessions_features.csv`. Verificado que a regeneração do dataset com `--seed 42` continua produzindo exatamente os mesmos valores de features (só os UUIDs, não determinísticos, mudam) — mesmo padrão de verificação já usado na extração de `simulator/events.py` (ADR 0007).

### 5. Uma conexão RabbitMQ e uma conexão SQLite por processo
Diferente do publisher (que abre/fecha uma conexão RabbitMQ por publicação), o subscriber abre uma única conexão/canal RabbitMQ na inicialização e a mantém durante todo o `start_consuming()` — padrão natural de um consumidor contínuo. Da mesma forma, mantém uma única conexão SQLite reaproveitada a cada mensagem: o callback de mensagem roda sempre na mesma thread do loop bloqueante do `pika`, então não há concorrência a proteger.

### 6. Ack somente após persistir; `prefetch_count=1`
A mensagem só é confirmada (`channel.basic_ack`) depois que a linha de features é gravada com sucesso no SQLite. Se a persistência falhar, a mensagem não é confirmada e permanece na fila; o processo encerra com erro explícito (sem engolir a exceção). `basic_qos(prefetch_count=1)` garante processamento estritamente sequencial (nunca mais de uma mensagem não confirmada por vez).

### 7. Mensagens malformadas: `basic_nack(requeue=False)`, sem dead-letter
Uma mensagem que não corresponda ao formato esperado (`player_id`, `session_id`, `events`, cada evento com os 7 campos de `events.csv`) é logada e descartada via `basic_nack(requeue=False)` — sem reencaminhar para a fila (evita loop de mensagem-veneno) e sem fila de dead-letter dedicada (fora do escopo deste protótipo).

## Consequências

- **Positivas**:
  - O pipeline simulador → RabbitMQ → worker → banco está completo e executável localmente (`make rabbitmq-up`, `make publisher`, `make subscriber`).
  - `player_features` acumula histórico auditável por jogador, pronto para o modelo de ML (change futura) consultar a linha mais recente com uma busca eficiente.
  - A lógica de agregação deixou de estar duplicada entre o script de dataset offline e o worker real.
- **Negativas / Limitações**:
  - Sem retry/backoff/dead-letter para mensagens que falham na persistência — aceitável para um protótipo local com reinício manual.
  - `player_features` sem FK para `users` — aceitável enquanto publisher/worker não dependem do fluxo de autenticação.
  - Tabela de histórico cresce indefinidamente, sem política de retenção — fora de escopo; volume esperado é baixo.
  - O endpoint `GET /players/{player_id}/persona` continua mockado nesta change; a integração real (consultar `player_features` + modelo de ML) é trabalho futuro.
