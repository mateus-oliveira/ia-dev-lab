# ADR 0007 - Simulador (worker publisher) e RabbitMQ

* **Status:** Aceito
* **Data:** 2026-09-11
* **Decisão:** Implementação do worker publisher (`src/player_modeling/simulator/`), que simula jogadores por persona da Taxonomia de Bartle e publica lotes de eventos brutos em uma única fila RabbitMQ (exchange default), rodando em loop contínuo para dois jogadores de teste fixos.

## Contexto

O escopo inicial do projeto (`docs/escopo.md`, "Objetivo inicial" do `CLAUDE.md`) prevê um simulador (cronjob) que gera eventos sintéticos e os publica em uma fila RabbitMQ, para que um worker separado (fora do escopo desta ADR) consuma, transforme e persista esses eventos no banco. Até esta decisão não havia RabbitMQ no projeto, nem lógica de simulação incremental — a única geração de eventos sintéticos era o script batch `src/player_modeling/scripts/generate_raw_events.py`, que gera uma sessão completa (20 a 80 eventos) por jogador, direto para `src/data/events.csv`, usada apenas para pré-treinar o modelo.

Esta ADR cobre somente a primeira metade do pipeline (simulador → RabbitMQ). O worker que consome da fila e persiste no banco será tratado em uma mudança futura; o formato de mensagem definido aqui é o contrato entre as duas partes.

## Decisões

### 1. Formato da mensagem: lote de eventos brutos, não features agregadas
Cada mensagem publicada é `{"player_id": str, "session_id": str, "events": [...]}`, onde cada evento tem exatamente as colunas de `src/data/events.csv` (`event_id`, `session_id`, `player_id`, `timestamp`, `event_type`, `decision_time_ms`, `outcome`). A alternativa de o publisher já enviar a linha agregada (estilo `sessions_features.csv`) foi descartada: agregar (contagem por tipo de evento, `fail_rate`, etc.) é responsabilidade do worker/ETL, mantendo a fronteira entre as duas branches clara. A mensagem **nunca** inclui a persona/`true_persona` do jogador simulado — isso é o que o modelo de ML vai prever a partir dos eventos, não um dado publicado na fila.

### 2. Janela de 15 a 20 eventos por mensagem
O dataset de treino (`sessions_features.csv`) tem `n_events` entre 20 e 80 por sessão. Uma janela muito menor (5 a 10, considerada inicialmente) faria o worker calcular features (`pct_attack`, `pct_explore`, etc.) sobre amostras bem menores que as vistas no treino, aumentando a variância dessas proporções e criando desvio treino/serving. Uma janela de 15 a 20 eventos reduz esse desvio sem exigir que o publisher acumule estado entre execuções do cronjob. Trade-off aceito: ainda é uma amostra menor que o topo da faixa de treino (80); se o modelo de perfil (mudança futura) performar mal, aumentar a janela é a primeira alternativa a revisitar.

### 3. Fila única, exchange default
Com um único produtor e um único tipo de mensagem, um exchange customizado (fanout/topic) não agrega valor neste protótipo. Uma fila durável (`RABBITMQ_QUEUE`, padrão `player_events`) publicada no exchange default do RabbitMQ (routing key = nome da fila) é suficiente e mais simples de operar e testar. Revisitar se, no futuro, mais de um tipo de mensagem ou mais de um consumidor por mensagem forem necessários.

### 4. Cliente RabbitMQ: `pika` (síncrono)
Cada publicação (uma por jogador, por ciclo) abre conexão, publica um lote e encerra — sequencialmente, sem concorrência a gerenciar. `pika` é a biblioteca síncrona de referência para RabbitMQ em Python; um cliente assíncrono (`aio-pika`) adicionaria a complexidade de um event loop sem benefício para este caso de uso, mesmo com o publisher rodando em loop contínuo (decisão 9).

### 5. Imagem Docker: `rabbitmq:3-management`
`docker-compose.yml` sobe o RabbitMQ com a variante `-management`, que inclui o painel web (porta `15672`) — útil neste projeto acadêmico para inspecionar a fila e as mensagens durante o desenvolvimento e a avaliação da disciplina. Custo aceito: imagem um pouco maior que `rabbitmq:3-alpine`, irrelevante para desenvolvimento local.

### 6. `session_id` por execução, sem estado persistente entre execuções
Cada execução do publisher gera um jogador simulado (`player_id` sintético) e um `session_id` novos (UUID). Não há tentativa de manter uma "sessão" contínua entre execuções do cronjob — isso exigiria o publisher consultar estado anterior, tornando-o stateful. O `session_id` só precisa ser único e consistente dentro da mensagem, não através de mensagens.

### 7. Geração de eventos por persona extraída para módulo compartilhado
A lógica de distribuição de eventos por persona (`PERSONA_PROFILES`, `session_weights`, geração de um lote de eventos), originalmente só em `src/player_modeling/scripts/generate_raw_events.py`, foi extraída para `src/player_modeling/simulator/events.py`. O script de geração do dataset offline passou a importar dessa nova localização em vez de duplicar a lógica — verificado que a regeneração do dataset com o mesmo `--seed` produz exatamente os mesmos valores de features (apenas os UUIDs, que já não eram determinísticos com o `random.seed` usado, mudam).

### 8. Credenciais via variáveis de ambiente, sem valores padrão hardcoded
Novas chaves (`RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USER`, `RABBITMQ_PASSWORD`, `RABBITMQ_QUEUE`) seguem o mesmo padrão de seção já usado para `DATABASE_PATH` (ADR 0004) e JWT (ADR 0005) no `.env.example`. O `docker-compose.yml` lê usuário/senha das mesmas variáveis (arquivo `.env` na raiz, carregado automaticamente pelo Docker Compose e pelo `Makefile`), evitando duplicar o segredo em dois lugares. Nenhuma dessas variáveis tem valor padrão hardcoded no código: se não estiverem definidas, o publisher falha explicitamente (`KeyError`) em vez de assumir um valor de desenvolvimento silencioso.

### 9. Execução contínua com loop interno, intervalo configurável via `PUBLISHER_INTERVAL_SECONDS`
Para permitir observar, na prática, como o perfil de um jogador de teste poderia oscilar ao longo de sucessivos ciclos de eventos, o publisher passou a rodar em loop (publica um ciclo, aguarda `PUBLISHER_INTERVAL_SECONDS`, repete) em vez de publicar uma única vez e encerrar. Alternativa considerada: manter o script one-shot e delegar o agendamento a uma ferramenta externa (`watch -n 60 make publisher`, cron do SO). Optou-se pelo loop interno por ser mais simples de rodar e observar localmente neste protótipo, sem exigir configuração de agendamento fora da aplicação; `make publisher` roda em primeiro plano até `Ctrl+C`. O intervalo é uma variável de ambiente obrigatória (sem default hardcoded), consistente com a decisão 8.

### 10. Jogadores de teste fixos via `PLAYER_USERNAME_1`/`PLAYER_USERNAME_2`, não mais `player_id` aleatório
Antes desta decisão, cada execução do publisher gerava um `player_id` sintético aleatório (`player_<uuid>`). Para permitir testar isolamento de dados entre contas conhecidas (ex.: duas contas criadas via `POST /auth/register`, consumidas depois pelo worker e pela API), o publisher agora usa exatamente dois `player_id` fixos, vindos de variáveis de ambiente, e publica um lote para cada um a cada ciclo. A função `build_player_batch()` (`simulator/batch.py`) continua aceitando `player_id` opcional com fallback aleatório — usado nos testes automatizados — mas o ponto de entrada do publisher (`main()`/`publish_cycle()`) sempre passa um dos dois usernames configurados. A persona de cada lote continua sendo sorteada aleatoriamente a cada ciclo (comportamento já existente, não alterado), o que faz o "perfil" de cada jogador de teste variar de ciclo para ciclo — é justamente esse comportamento que permite observar a oscilação do perfil previsto (quando o worker/modelo existirem).

## Consequências

- **Positivas**:
  - O pipeline simulador → RabbitMQ existe e é executável localmente (`make rabbitmq-up`, `make publisher`), pronto para o worker subscriber (mudança futura) consumir.
  - O formato de mensagem e a janela de eventos ficam documentados como contrato entre as duas branches, reduzindo o risco de divergência.
  - A lógica de geração de eventos por persona deixou de estar duplicada entre o script de dataset offline e o simulador.
  - Rodar `make publisher` já produz, sozinho, um fluxo contínuo de eventos para dois jogadores de teste conhecidos, útil para validar isolamento de dados e observar variação de perfil assim que o worker/modelo existirem.
- **Negativas / Limitações**:
  - Sem retry/backoff caso o broker esteja indisponível quando um ciclo do publisher rodar — aceitável para um protótipo local; a falha é explícita e o próximo ciclo tenta novamente (se o processo continuar rodando) ou o operador reinicia manualmente.
  - Nenhuma validação de schema da mensagem do lado do consumidor ainda existe (não há consumidor); a mudança do worker subscriber deve validar contra o mesmo contrato.
  - A janela de 15-20 eventos ainda é menor que o topo da faixa vista no treino (80), com o risco de desvio treino/serving descrito na decisão 2.
  - O publisher agora é um processo de longa duração em vez de um cronjob one-shot — se o objetivo futuro for rodá-lo via um agendador externo (cron real, Kubernetes CronJob), o modo de loop interno precisará ser revisitado (ex.: flag para rodar um único ciclo e encerrar).
