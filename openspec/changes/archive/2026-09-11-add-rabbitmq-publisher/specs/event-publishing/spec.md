## Purpose

Publicar, em uma fila RabbitMQ, lotes de eventos sintéticos recentes de um jogador simulado, no formato que o worker/ETL (fora do escopo desta capability) consumirá para gerar as features usadas pelo modelo de perfil Bartle.

## ADDED Requirements

### Requirement: Fila única com exchange default
O sistema SHALL publicar todas as mensagens de eventos em uma única fila RabbitMQ durável, utilizando o exchange default (routing key igual ao nome da fila), sem depender de um exchange customizado.

#### Scenario: Fila inexistente no primeiro uso
- **WHEN** o publisher é executado contra um broker RabbitMQ que ainda não tem a fila declarada
- **THEN** a fila é declarada como durável antes da publicação, e a mensagem é publicada nela com sucesso

#### Scenario: Reinício do broker
- **WHEN** o container RabbitMQ é reiniciado após a fila já ter sido declarada
- **THEN** a fila e suas mensagens não confirmadas (ack) persistem, por ser uma fila durável

### Requirement: Mensagem de lote de eventos por jogador
O sistema SHALL publicar, a cada execução do simulador, uma mensagem JSON contendo o `player_id`, um `session_id` e uma lista de 15 a 20 eventos recentes desse jogador, cada evento no mesmo formato de uma linha de `src/data/events.csv` (`event_id`, `session_id`, `player_id`, `timestamp`, `event_type`, `decision_time_ms`, `outcome`).

#### Scenario: Publicação de um lote válido
- **WHEN** o simulador gera eventos para um jogador simulado
- **THEN** a mensagem publicada contém entre 15 e 20 eventos, todos com o mesmo `player_id` e `session_id` da mensagem

#### Scenario: Mensagem nunca revela a persona simulada
- **WHEN** o simulador gera eventos a partir de uma persona da Taxonomia de Bartle (Killer, Achiever, Socializer ou Explorer) para moldar as probabilidades de tipo de evento
- **THEN** a mensagem publicada na fila não contém a persona nem qualquer campo equivalente a `true_persona` — apenas os eventos e os identificadores do jogador/sessão

### Requirement: Eventos apenas sintéticos
O sistema SHALL gerar exclusivamente eventos sintéticos, sem qualquer dado pessoal, identificável ou proveniente de jogadores reais.

#### Scenario: Identificador de jogador simulado
- **WHEN** o simulador cria um novo jogador simulado
- **THEN** o `player_id` gerado é um identificador sintético (sem nome, e-mail ou qualquer dado que identifique uma pessoa real)

### Requirement: Execução periódica contínua
O publisher SHALL, quando executado, publicar ciclos de lotes de eventos repetidamente em um intervalo configurável, em vez de encerrar após uma única publicação, permitindo observar como o perfil de um jogador evolui ao longo de sucessivos ciclos de eventos.

#### Scenario: Execução contínua até interrupção
- **WHEN** o publisher é iniciado (ex.: `make publisher`)
- **THEN** ele publica um ciclo de lotes, aguarda o intervalo configurado em `PUBLISHER_INTERVAL_SECONDS` e repete indefinidamente, até ser interrompido manualmente (ex.: Ctrl+C)

### Requirement: Jogadores de teste fixos e configuráveis
O sistema SHALL publicar, em cada ciclo, um lote de eventos para cada um dos dois jogadores de teste identificados pelas variáveis de ambiente `PLAYER_USERNAME_1` e `PLAYER_USERNAME_2`, em vez de gerar um `player_id` aleatório a cada execução, permitindo testar isolamento de dados entre contas conhecidas (ex.: criadas via `POST /auth/register`).

#### Scenario: Ciclo publica para os dois jogadores configurados
- **WHEN** um ciclo do publisher é executado com `PLAYER_USERNAME_1` e `PLAYER_USERNAME_2` configurados no ambiente
- **THEN** duas mensagens são publicadas nesse ciclo: uma com `player_id` igual a `PLAYER_USERNAME_1` e outra com `player_id` igual a `PLAYER_USERNAME_2`, cada uma com sua própria persona sorteada independentemente

#### Scenario: Variável de ambiente ausente
- **WHEN** `PLAYER_USERNAME_1` ou `PLAYER_USERNAME_2` não está definida no ambiente
- **THEN** o publisher falha de forma explícita ao tentar montar o ciclo, em vez de publicar com um identificador de jogador inventado
