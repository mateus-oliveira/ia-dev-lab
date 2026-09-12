## Context

Ver `proposal.md` - Why. O contrato de mensagem já está fixado pela change `add-rabbitmq-publisher` (arquivada): `{"player_id": str, "session_id": str, "events": [...]}`, com `events` no formato de `src/data/events.csv`, publicado em uma fila única (`RABBITMQ_QUEUE`) durável, exchange default. O publisher roda continuamente, publicando para `PLAYER_USERNAME_1`/`PLAYER_USERNAME_2` a cada `PUBLISHER_INTERVAL_SECONDS`.

O acesso a dados em runtime no projeto é `sqlite3` puro (não SQLAlchemy Core/ORM) via `api/database.py::get_connection()`; Alembic (SQLAlchemy apenas nas migrações) gerencia o schema, com migrações escritas manualmente (ADR 0006). O único schema hoje é a tabela `users` (ADR 0004).

Duas decisões de arquitetura já foram tomadas diretamente com o desenvolvedor antes desta proposta (não são escolhas em aberto):
1. O subscriber é um consumidor **contínuo** (long-running, `pika` `basic_consume`), não um cronjob one-shot que drena a fila e encerra.
2. O armazenamento é uma **tabela única de histórico** (`player_features`, 1 jogador : N linhas) com um **índice composto em `(player_id, id)`** para busca eficiente da linha mais recente — não uma segunda tabela de cache 1:1 sincronizada.

## Goals / Non-Goals

**Goals:**
- Consumir a fila continuamente e persistir uma linha de features por mensagem processada, sem perder mensagens em caso de falha de persistência (ack somente após persistir com sucesso).
- Reaproveitar a lógica de agregação já usada para gerar `sessions_features.csv`, sem duplicá-la.
- Manter o subscriber simples de operar localmente (`make subscriber`), simétrico ao `make publisher` já existente.

**Non-Goals:**
- Treinar ou executar um modelo de ML — fora do escopo (módulo `ml/` continua vazio).
- Expor a nova tabela via API — o endpoint `GET /players/{player_id}/persona` continua mockado nesta change.
- Lidar com múltiplos consumidores concorrentes na mesma fila, alta disponibilidade ou reprocessamento automático de mensagens rejeitadas (fila de dead-letter) — fora do escopo de um protótipo local com um único consumidor.

## Decisions

### 1. Tabela `player_features`: histórico único + índice composto `(player_id, id)`
Decisão já tomada com o desenvolvedor (ver Context). Esquema:

| Coluna | Tipo | Observação |
| --- | --- | --- |
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | ordem de inserção, usado para "mais recente" em vez de `created_at` (evita colisão/precisão de timestamp) |
| `player_id` | `TEXT NOT NULL` | sem FK para `users.username` nesta change — o subscriber persiste features de qualquer `player_id` recebido na fila, independente de existir cadastro |
| `session_id` | `TEXT NOT NULL` | vem da mensagem |
| `n_events` | `INTEGER NOT NULL` | |
| `pct_attack`, `pct_explore`, `pct_social`, `pct_quest_complete`, `pct_retry`, `fail_rate` | `REAL NOT NULL` | proporções, mesmas colunas de `sessions_features.csv` |
| `avg_decision_time_ms` | `REAL NOT NULL` | |
| `created_at` | `TEXT NOT NULL` | ISO 8601, gerado em Python (`datetime.now(UTC).isoformat()`) no momento da persistência — consistente com o formato de timestamp já usado em `events.csv` |

Índice: `CREATE INDEX ix_player_features_player_id_id ON player_features (player_id, id)`. A consulta "linha mais recente de um jogador" (`SELECT * FROM player_features WHERE player_id = ? ORDER BY id DESC LIMIT 1`) usa esse índice para localizar as linhas do jogador e pegar o maior `id` sem varrer a tabela inteira.

**Alternativa descartada** (já discutida com o desenvolvedor): tabela `player_features` (histórico) + tabela `player_latest_features` (1:1 com jogador, sobrescrita a cada mensagem) para tornar a busca O(1). Rejeitada por introduzir *dual-write* (toda inserção no histórico exigiria um upsert sincronizado na tabela "latest", na mesma transação) para um ganho de performance irrelevante na escala deste protótipo (poucas dezenas de milhares de linhas mesmo após meses de execução contínua).

**Alternativa possível no futuro, não implementada agora**: uma `VIEW` SQL computando a linha mais recente por jogador sob demanda, sem duplicar dados — útil se a consulta "latest" passar a ser usada em vários lugares. Hoje só o futuro endpoint usaria essa consulta, então a view seria complexidade antecipada sem necessidade concreta ainda.

### 2. Sem chave estrangeira para `users`
`player_features.player_id` é apenas `TEXT`, sem `FOREIGN KEY` para `users.username`. O worker deve conseguir persistir eventos de qualquer jogador simulado, mesmo que o cadastro via `/auth/register` ainda não tenha sido feito (o publisher e o worker são independentes do fluxo de autenticação). Revisitar se, no futuro, a API passar a exigir que todo `player_id` com features corresponda a um usuário cadastrado.

### 3. Extração de `extract_features()` para `worker/features.py`, sem persona
A lógica de agregação (hoje só em `scripts/generate_raw_events.py::extract_features`) muda de assinatura ao ser extraída: a versão compartilhada (`worker/features.py::extract_features(session_id, player_id, events)`) **não recebe nem retorna** `persona`/`true_persona` — esse rótulo não existe nas mensagens reais consumidas da fila. `generate_raw_events.py` passa a chamar essa função e depois adicionar `true_persona` ao dicionário retornado, por fora, só para compor `sessions_features.csv` (dataset de treino). Isso espelha o padrão já usado para a geração de eventos (`simulator/events.py`), evitando duplicar a lógica de agregação entre o script offline e o worker real.

### 4. Uma conexão RabbitMQ e uma conexão SQLite por processo, reaproveitadas entre mensagens
Diferente do publisher (que abre/fecha uma conexão RabbitMQ por publicação, adequado a chamadas isoladas), o subscriber abre **uma única conexão RabbitMQ** (e um único canal) na inicialização e a mantém durante todo o `start_consuming()` — é o padrão natural de um consumidor contínuo via `pika`. Da mesma forma, mantém **uma única conexão SQLite** aberta durante todo o processo, reaproveitada a cada mensagem processada (o callback de mensagem roda sempre na mesma thread do loop bloqueante do `pika`, então não há concorrência a proteger).

### 5. Ack somente após persistir com sucesso; `basic_qos(prefetch_count=1)`
O `ack` da mensagem (`channel.basic_ack`) só ocorre depois que a linha de features é gravada com sucesso no SQLite — se a persistência falhar (exceção), a mensagem não é confirmada e permanece na fila para nova tentativa (o processo encerra com erro explícito; ver Riscos). `prefetch_count=1` garante que o subscriber não puxe mais de uma mensagem não confirmada por vez do broker, mantendo o processamento estritamente sequencial e simples de raciocinar.

### 6. Mensagens malformadas: `basic_nack(requeue=False)` sem dead-letter
Uma mensagem que falhe ao ser interpretada como `{player_id, session_id, events}` (JSON inválido, campos ausentes, tipos incorretos) é logada e descartada via `basic_nack(delivery_tag, requeue=False)` — sem reencaminhar para a fila (evitando loop de mensagem-veneno) e sem fila de dead-letter dedicada (fora do escopo deste protótipo; se necessário revisitar, configurar `x-dead-letter-exchange` na fila).

### 7. Graceful shutdown com `Ctrl+C`
`main()` chama `channel.start_consuming()` dentro de um `try`; um `KeyboardInterrupt` é capturado, chama `channel.stop_consuming()` e fecha a conexão em um `finally` — padrão recomendado pelo `pika` para encerrar um consumidor bloqueante sem deixar a conexão em estado inconsistente.

## Risks / Trade-offs

- **Falha de persistência mantém a mensagem não confirmada indefinidamente** (decisão 5) → Mitigação: a falha é explícita (o processo não engole a exceção); como é um protótipo local com reinício manual, aceitável. Revisitar com retry/backoff ou dead-letter se o worker precisar rodar de forma não supervisionada.
- **Sem validação de schema formal da mensagem** (apenas checagem estrutural dos campos esperados) → Mitigação: o contrato já está fixado na spec da change do publisher; validação estrutural simples (presença e tipo dos três campos) é suficiente para este protótipo.
- **`player_features` sem FK para `users`** (decisão 2) → Mitigação: aceitável enquanto publisher/worker não dependem do fluxo de autenticação; revisitar se a integração do endpoint real (change futura) exigir consistência referencial.
- **Tabela de histórico cresce indefinidamente** (nenhuma política de retenção/purge) → Mitigação: fora de escopo para um protótipo local; volume esperado é baixo (poucas linhas por minuto).

## Migration Plan

Não há dados existentes em `player_features` a migrar (tabela nova). Passos de adoção:
1. `poetry run alembic upgrade head` (ou `make migrate`) aplica a nova migração.
2. `make rabbitmq-up` + `make publisher` (já existentes) alimentam a fila.
3. `make subscriber` consome e persiste continuamente.

Rollback: `poetry run alembic downgrade -1` remove a tabela `player_features` (sem afetar `users`); reverter o commit remove o código do worker.
