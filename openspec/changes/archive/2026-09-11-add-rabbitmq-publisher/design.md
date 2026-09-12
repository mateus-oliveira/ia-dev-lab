## Context

Ver `proposal.md` - Why. Hoje não existe RabbitMQ no projeto nem lógica de simulação incremental: a única geração de eventos sintéticos é o script batch `src/player_modeling/scripts/generate_raw_events.py`, que gera uma sessão completa (20-80 eventos) por jogador, direto para CSV, com `PERSONA_PROFILES` guiando a distribuição de tipos de evento por persona. Essa lógica de geração por persona é a base a ser reaproveitada pelo publisher; não deve ser duplicada.

O worker/ETL que vai consumir esta fila é uma change futura, mas o formato da mensagem definido aqui vira um contrato entre as duas branches — por isso está fixado em `specs/event-publishing/spec.md` (capability `event-publishing`) e detalhado aqui.

## Goals / Non-Goals

**Goals:**
- Definir um formato de mensagem estável para o worker futuro consumir, sem acoplar o publisher a como o worker vai agregar os dados.
- Rodar localmente (docker-compose) sem exigir infraestrutura de produção.
- Manter o publisher simples, sem estado persistente próprio entre ciclos de publicação.
- Permitir observar, manualmente, como o perfil de um jogador de teste evoluiria ao longo de vários ciclos de eventos (execução contínua com intervalo configurável).

**Non-Goals:**
- Consumir da fila (worker/ETL) — change futura.
- Garantir entrega exactly-once ou lidar com fila cheia/backpressure — fora do escopo de um protótipo com um único produtor.
- Rodar o RabbitMQ fora do `docker-compose` local (produção/deploy).

## Decisions

### 1. Formato da mensagem: lote de eventos brutos, não features agregadas
A mensagem publicada é `{"player_id": str, "session_id": str, "events": [...]}`, onde cada item de `events` tem exatamente as colunas de `src/data/events.csv`. A alternativa considerada — o publisher já enviar a linha agregada (estilo `sessions_features.csv`) — foi descartada porque a agregação (contagem por tipo de evento, `fail_rate`, etc.) é responsabilidade do worker/ETL (ver `docs/escopo.md`, etapa 2 do fluxo); o publisher só gera e envia eventos brutos, mantendo a fronteira entre as duas branches clara e testável.

### 2. Janela de 15 a 20 eventos por mensagem
O dataset de treino (`sessions_features.csv`) tem `n_events` entre 20 e 80 por sessão. Enviar lotes muito menores (ex.: 5-10, considerado inicialmente) faria o worker calcular features (`pct_attack`, `pct_explore`, etc.) sobre amostras bem menores que as vistas no treino, aumentando a variância dessas proporções e criando desvio treino/serving. Uma janela de 15-20 eventos reduz esse desvio sem exigir que o publisher acumule estado entre execuções do cronjob. Trade-off aceito: ainda é uma amostra menor que o topo da faixa de treino (80); se o modelo (change futura) performar mal, aumentar a janela é a primeira alternativa a revisitar.

### 3. Fila única, exchange default
Com um único produtor e um único tipo de mensagem, um exchange customizado (fanout/topic) não agrega valor neste protótipo. Uma fila durável no exchange default (routing key = nome da fila) é suficiente e mais simples de operar/testar. Revisitar se, no futuro, mais de um tipo de mensagem ou mais de um consumidor por mensagem forem necessários.

### 4. Cliente RabbitMQ: `pika` (síncrono) em vez de `aio-pika`
Cada publicação (uma por jogador, por ciclo) abre conexão, publica um lote e encerra — sequencialmente, sem concorrência a gerenciar. Um cliente assíncrono (`aio-pika`) adicionaria complexidade (event loop) sem benefício. `pika` é a biblioteca síncrona de referência para RabbitMQ em Python e é suficiente aqui, mesmo com o publisher rodando em loop contínuo (decisão 8).

### 5. Imagem Docker: `rabbitmq:3-management`
A variante `-management` inclui o painel web (porta `15672`), útil neste projeto acadêmico para inspecionar a fila/mensagens durante o desenvolvimento e a avaliação da disciplina. Custo aceito: imagem um pouco maior que `rabbitmq:3-alpine`, irrelevante para um ambiente de desenvolvimento local.

### 6. `session_id` gerado pelo publisher, sem estado persistente entre execuções
Cada execução do publisher gera um `session_id` novo (UUID) para o lote publicado naquela execução — não há tentativa de manter uma "sessão" contínua entre execuções do cronjob (isso exigiria o publisher consultar estado anterior, o que o tornaria stateful). Isso é consistente com o worker também sendo stateless por mensagem (cada mensagem processada vira uma linha independente, decisão que pertence à change do worker, mas que restringe o contrato aqui: o `session_id` só precisa ser único e consistente dentro da mensagem, não através de mensagens).

### 7. Credenciais RabbitMQ via variáveis de ambiente, seguindo o padrão do `.env.example`
Novas chaves (`RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USER`, `RABBITMQ_PASSWORD`, `RABBITMQ_QUEUE`) seguem o mesmo padrão de seção já usado para `DATABASE_PATH` (ADR 0004) e JWT (ADR 0005) no `.env.example`. O `docker-compose.yml` lê usuário/senha dessas mesmas variáveis (via `env_file: .env` ou equivalente), evitando duplicar o segredo em dois lugares. Nenhuma dessas variáveis tem valor padrão hardcoded no código: se não estiverem definidas, o publisher falha explicitamente (`KeyError`) em vez de assumir um valor de desenvolvimento silencioso.

### 8. Execução contínua com loop interno, intervalo configurável via `PUBLISHER_INTERVAL_SECONDS`
Para observar como o perfil de um jogador evoluiria ao longo de sucessivos ciclos de eventos, o publisher passou a rodar em loop (publica um ciclo, aguarda `PUBLISHER_INTERVAL_SECONDS`, repete) em vez de publicar uma única vez e encerrar. Alternativa considerada: manter o script one-shot e delegar o agendamento a uma ferramenta externa (`watch -n 60 make publisher`, cron do SO). Optou-se pelo loop interno por ser mais simples de rodar e observar localmente neste protótipo, sem exigir configuração de agendamento fora da aplicação; `make publisher` roda em primeiro plano até `Ctrl+C`. O intervalo é uma variável de ambiente obrigatória (sem default hardcoded), consistente com a decisão 7.

### 9. Jogadores de teste fixos via `PLAYER_USERNAME_1`/`PLAYER_USERNAME_2`, não mais `player_id` aleatório
Antes desta decisão, cada execução do publisher gerava um `player_id` sintético aleatório (`player_<uuid>`). Para permitir testar isolamento de dados entre contas conhecidas (ex.: duas contas criadas via `POST /auth/register`, consumidas depois pelo worker e pela API), o publisher agora usa exatamente dois `player_id` fixos, vindos de variáveis de ambiente, e publica um lote para cada um a cada ciclo. A função `build_player_batch()` (`simulator/batch.py`) continua aceitando `player_id` opcional com fallback aleatório — usado nos testes automatizados — mas o ponto de entrada do publisher (`main()`) sempre passa um dos dois usernames configurados. A persona de cada lote continua sendo sorteada aleatoriamente a cada ciclo (comportamento já existente, não alterado), o que faz o "perfil" de cada jogador de teste variar de ciclo para ciclo — é justamente esse comportamento que permite observar a oscilação do perfil previsto (quando o worker/modelo existirem).

## Risks / Trade-offs

- **Desvio treino/serving nas features** (janela de 15-20 vs. 20-80 no treino) → Mitigação: decisão 2 acima; revisitar tamanho da janela se o modelo (change futura) tiver métricas ruins em produção comparado à validação offline.
- **Broker indisponível quando o publisher roda** (container não subido) → Mitigação: falha explícita e visível (o script não deve engolir a exceção de conexão); como é um cronjob, a próxima execução tenta novamente. Não há retry/backoff nesta change por ser um protótipo local.
- **Nenhuma validação de schema da mensagem no lado do consumidor** (não existe ainda) → Mitigação: o formato está fixado em `specs/event-publishing/spec.md` como contrato entre as branches; a change do worker deve validar contra esse mesmo contrato.
- **Loop interno derruba a conexão em execuções longas** (o processo fica em primeiro plano por tempo indefinido) → Mitigação: cada publicação abre e fecha sua própria conexão (decisão 4), então uma falha de conexão em um ciclo não corrompe o estado do processo; o próximo ciclo tenta se conectar novamente. Não há reconexão automática dentro do mesmo ciclo — se falhar, o erro sobe e o processo encerra (o operador reinicia manualmente).

## Migration Plan

Não aplicável a dados existentes (não há schema de banco alterado nesta change). Passos de adoção:
1. `docker compose up -d` sobe o RabbitMQ.
2. `poetry install` traz a nova dependência `pika`.
3. Copiar as novas chaves de `.env.example` para `.env` (com as credenciais desejadas).
4. Rodar o publisher (comando definido em `tasks.md`/README) para publicar mensagens de teste.

Rollback: `docker compose down` remove o container; reverter o commit remove a dependência e o código do publisher. Nenhum dado em `src/data/` é afetado.
