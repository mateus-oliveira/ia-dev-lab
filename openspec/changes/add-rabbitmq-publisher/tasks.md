## 1. Infraestrutura RabbitMQ

- [x] 1.1 Criar `docker-compose.yml` na raiz com o serviço RabbitMQ (`rabbitmq:3-management`), lendo usuário/senha de variáveis de ambiente, e verificar que `docker compose up -d` sobe o container e o painel web fica acessível em `http://localhost:15672`.
- [x] 1.1.1 Adicionar ao `Makefile` o alvo `rabbitmq-up` (`docker compose up -d`), documentá-lo no `help` seguindo o padrão dos alvos existentes (`migrate`, `run`, etc.), e verificar que `make rabbitmq-up` sobe o container.
- [x] 1.2 Adicionar ao `.env.example` uma seção "RabbitMQ" com `RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USER`, `RABBITMQ_PASSWORD`, `RABBITMQ_QUEUE`, seguindo o padrão das seções existentes (ADR 0004/0005), e replicar essas chaves com valores locais no `.env`.
- [x] 1.3 Adicionar a dependência `pika` ao `pyproject.toml` via Poetry e verificar que `poetry install` conclui sem erro e `poetry run python -c "import pika"` funciona.

## 2. Módulo simulator/publisher

- [x] 2.1 Criar um módulo de geração de eventos por persona em `src/player_modeling/simulator/` reaproveitando `PERSONA_PROFILES`/`session_weights`/geração de evento de `src/player_modeling/scripts/generate_raw_events.py` (extrair para função(ões) compartilhada(s) em vez de duplicar o código), com type hints e docstrings no formato do `CLAUDE.md`.
- [x] 2.2 Implementar a função que monta a mensagem `{player_id, session_id, events}` com uma janela de 15 a 20 eventos, garantindo que nenhum campo de persona/`true_persona` seja incluído.
- [x] 2.3 Implementar o cliente de publicação (conexão `pika`, declaração da fila durável via exchange default, publicação da mensagem serializada em JSON) em um módulo separado (ex.: `src/player_modeling/simulator/publisher.py`), lendo host/porta/usuário/senha/fila das variáveis de ambiente definidas na tarefa 1.2.
- [x] 2.4 Expor um ponto de entrada executável (script/CLI) para rodar o publisher manualmente ou via cronjob, e verificar manualmente (com o RabbitMQ da tarefa 1.1 no ar) que uma mensagem aparece na fila pelo painel de management.
- [x] 2.5 Adicionar ao `Makefile` o alvo `publisher` (roda o ponto de entrada da tarefa 2.4 via `poetry run`), documentá-lo no `help` substituindo o comentário placeholder "Alvos de worker/simulador... serão adicionados aqui" por um indicando que `subscriber` será adicionado na branch do worker subscriber, e verificar que `make publisher` publica uma mensagem na fila (com `make rabbitmq-up` já executado).

## 2.6 Execução contínua e jogadores de teste fixos

- [x] 2.6.1 Adicionar ao `.env.example`/`.env` as variáveis `PLAYER_USERNAME_1`, `PLAYER_USERNAME_2` e `PUBLISHER_INTERVAL_SECONDS`, sem valores padrão hardcoded no código (consistente com a tarefa 1.2).
- [x] 2.6.2 Implementar em `publisher.py` a leitura de `PLAYER_USERNAME_1`/`PLAYER_USERNAME_2`/`PUBLISHER_INTERVAL_SECONDS` e uma função de "ciclo" que publica um lote (`build_player_batch` + `publish_batch`) para cada um dos dois jogadores configurados.
- [x] 2.6.3 Alterar o ponto de entrada (`main()`) para rodar o ciclo em loop, aguardando o intervalo configurado entre ciclos, até ser interrompido (`Ctrl+C`), em vez de publicar uma única vez e encerrar.
- [x] 2.6.4 Verificar manualmente (RabbitMQ no ar) que `make publisher` publica repetidamente mensagens para os dois `PLAYER_USERNAME_*` configurados, respeitando o intervalo, e encerra de forma limpa com `Ctrl+C`.

## 3. Testes

- [x] 3.1 Criar `src/tests/player_modeling/simulator/test_events.py` cobrindo a geração de eventos por persona (quantidade de eventos na janela 15-20, formato de cada evento igual ao de `events.csv`) e verificar que `poetry run pytest src/tests/player_modeling/simulator/test_events.py` passa.
- [x] 3.2 Criar `src/tests/player_modeling/simulator/test_publisher.py` cobrindo a montagem da mensagem (ausência de persona/`true_persona`, `player_id`/`session_id` consistentes entre os eventos) e a chamada de publicação mockando a conexão `pika` (sem broker real), e verificar que `poetry run pytest src/tests/player_modeling/simulator/test_publisher.py` passa.
- [x] 3.4 Criar/estender testes cobrindo o ciclo de publicação (um lote para cada `PLAYER_USERNAME_*` configurado) e o loop do publisher (com o intervalo mockado/reduzido, sem depender de um broker real nem de esperar o intervalo de verdade).
- [x] 3.3 Rerodar `poetry run pytest` (suíte completa) e `poetry run ruff check .` / `poetry run mypy .` após a tarefa 2.6, e verificar que tudo passa sem regressões.

## 4. Documentação

- [x] 4.1 Criar `docs/adr/0007-simulador-publisher-rabbitmq.md` documentando as decisões de `design.md` (fila única + exchange default, formato da mensagem, janela de 15-20 eventos, `pika` síncrono, imagem `rabbitmq:3-management`).
- [x] 4.2 Atualizar `CLAUDE.md` (seção "Comandos") e `README.md` com os comandos para subir o RabbitMQ (`docker compose up -d`) e executar o publisher, e verificar que os comandos documentados funcionam como descrito.
- [x] 4.3 Atualizar ADR 0007, `CLAUDE.md` e `README.md` para descrever a execução contínua (loop + `PUBLISHER_INTERVAL_SECONDS`) e os jogadores de teste fixos (`PLAYER_USERNAME_1`/`PLAYER_USERNAME_2`).
