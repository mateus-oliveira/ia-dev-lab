# player-feature-ingestion Specification

## Purpose

Consumir continuamente os lotes de eventos publicados na fila RabbitMQ, agregá-los em features por jogador e persistir um histórico dessas features no banco de dados, para que um modelo de ML (fora do escopo desta capability) possa futuramente prever o perfil do jogador na Taxonomia de Bartle a partir da linha mais recente.

## Requirements

### Requirement: Consumo contínuo da fila
O worker subscriber SHALL consumir mensagens da fila configurada (`RABBITMQ_QUEUE`) continuamente, processando cada mensagem assim que ela chega, em vez de encerrar após esvaziar a fila uma única vez.

#### Scenario: Mensagens publicadas enquanto o subscriber está rodando
- **WHEN** o subscriber está em execução e uma nova mensagem é publicada na fila
- **THEN** a mensagem é consumida e processada sem que o subscriber precise ser reiniciado

#### Scenario: Interrupção manual
- **WHEN** o operador interrompe o processo do subscriber (ex.: `Ctrl+C`)
- **THEN** o processo encerra sem deixar a mensagem em processamento naquele momento em estado inconsistente (a mensagem é reconhecida — *ack* — somente após a persistência ter sido concluída com sucesso)

### Requirement: Agregação de eventos em features por lote
O sistema SHALL transformar cada mensagem consumida (contendo `player_id`, `session_id` e uma lista de eventos) em uma única linha de features agregadas: `n_events`, `pct_attack`, `pct_explore`, `pct_social`, `pct_quest_complete`, `pct_retry`, `avg_decision_time_ms`, `fail_rate`. Essa linha NÃO SHALL conter persona ou qualquer rótulo equivalente a `true_persona`.

#### Scenario: Lote de eventos válido é agregado corretamente
- **WHEN** uma mensagem com uma lista de eventos é consumida
- **THEN** a linha de features resultante reflete exatamente as proporções e médias calculadas sobre aqueles eventos, sem depender de nenhuma informação externa à mensagem

### Requirement: Histórico persistido por jogador
O sistema SHALL persistir cada linha de features agregadas como um novo registro no banco de dados, associado ao `player_id` da mensagem, preservando o histórico de todas as linhas processadas anteriormente para aquele jogador (não sobrescrever registros existentes).

#### Scenario: Duas mensagens do mesmo jogador
- **WHEN** duas mensagens consecutivas do mesmo `player_id` são processadas
- **THEN** existem duas linhas distintas no banco de dados para aquele `player_id`, cada uma com sua própria linha de features

#### Scenario: Consulta da linha mais recente de um jogador
- **WHEN** é necessário obter a linha de features mais recente de um `player_id` (uso futuro, fora do escopo desta capability)
- **THEN** essa consulta pode ser respondida de forma eficiente (sem varrer todo o histórico), graças a um índice que suporta a busca por `player_id` ordenada pela ordem de inserção

### Requirement: Mensagens malformadas não interrompem o consumo
O sistema SHALL descartar, sem reprocessar, qualquer mensagem que não corresponda ao formato esperado (`player_id`, `session_id`, `events`), registrando a ocorrência, e SHALL continuar consumindo as mensagens seguintes da fila.

#### Scenario: Mensagem com JSON inválido ou campos ausentes
- **WHEN** uma mensagem que não pode ser interpretada como o formato esperado é consumida
- **THEN** ela é descartada (confirmada/*ack* junto ao broker, sem retorno à fila) e o subscriber continua consumindo normalmente as próximas mensagens, sem encerrar nem travar
