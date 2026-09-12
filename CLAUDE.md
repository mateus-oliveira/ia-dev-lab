# **Player Modeling Lab**

## Sobre o projeto

### Objetivo

Este projeto é uma Prova de Conceito (POC) para experimentação de **Player Modeling**, com foco na utilização de Engenharia de Dados e Machine Learning para representar e analisar o comportamento de jogadores.

O projeto terá evolução incremental ao longo da disciplina **PPGTI1101** utilizando ferramentas de Inteligência Artificial como apoio ao desenvolvimento, análise, testes, documentação e evolução da arquitetura.

### Objetivo inicial

A primeira versão do projeto deve implementar, com o auxílio de IA, um repositório Python responsável por:

1. rodar um **simulador** (cronjob) que gera eventos sintéticos de jogadores e os publica em uma fila **RabbitMQ**;
2. rodar um **worker** (outro cronjob) que consome os eventos da fila, transforma-os e os persiste em um banco de dados (processo de ETL);
3. disponibilizar ao menos um **endpoint GET** que, a partir dos eventos mais recentes de um jogador, retorna o perfil previsto por um modelo de Machine Learning segundo a **Taxonomia de Bartle** (`Killer`, `Achiever`, `Socializer`, `Explorer`).

Esta versão não inclui frontend nem autenticação/autorização.

Fluxo inicial:

```text
Simulador (cronjob)
      ↓
   RabbitMQ
      ↓
Worker / ETL (cronjob)
      ↓
Banco de dados
      ↓
Modelo de ML (Taxonomia de Bartle)
      ↓
Endpoint GET (perfil do jogador)
```

Enquanto o pipeline real (simulador → RabbitMQ → worker) não está pronto, o modelo de ML é pré-treinado com o dataset sintético gerado por `src/player_modeling/scripts/generate_raw_events.py` (`src/data/events.csv` e `src/data/sessions_features.csv`, este último já rotulado com `true_persona` para treino supervisionado).

### Evolução planejada

O escopo inicial já cobre simulador, worker/ETL, banco de dados, modelo de ML e endpoint de consulta (ver "Objetivo inicial"). Futuras versões poderão adicionar:

* endpoints adicionais além do GET de consulta de perfil;
* frontend para visualização dos perfis;
* autenticação e autorização;
* análise de importância das features;
* técnicas de explicabilidade;
* integração com fontes externas de eventos, como plataformas de jogos reais;
* experimentos adicionais de Player Modeling.

Essas funcionalidades **não devem ser implementadas antecipadamente** sem uma solicitação explícita.

---

## Comandos

### Instalar dependências

O projeto usa [Poetry](https://python-poetry.org/), que cria automaticamente um virtualenv em `.venv/` (configurado via `poetry.toml`, dentro do projeto):

```bash
poetry install
```

### Ativar os hooks de pré-commit (harness)

```bash
poetry run pre-commit install
poetry run pre-commit install --hook-type commit-msg
```

Formatação, lint, verificação de tipos, testes rápidos, validação da mensagem de commit, validação da branch atual e checagem de arquivos sensíveis rodam automaticamente antes de cada commit (ver `docs/adr/0003-harness-desenvolvimento.md`).

### Executar testes

```bash
poetry run pytest
```

### Executar um teste específico

```bash
poetry run pytest src/tests/test_nome_do_teste.py
```

### Rodar as verificações do harness manualmente

```bash
poetry run ruff check .
poetry run ruff format .
poetry run mypy .
poetry run pre-commit run --all-files
```

### Relatório de alterações fora do escopo

Antes de concluir uma tarefa, liste os arquivos alterados em relação à branch base (`dev` por padrão) e confira se não há alterações acidentais em dados brutos ou configurações:

```bash
poetry run python scripts/report_scope_diff.py [branch-base]
```

### Executar o pipeline

O pipeline tem três pontos de entrada: simulador (cronjob), worker/ETL (cronjob) e API (endpoint GET).

Gerar o dataset sintético usado para pré-treinar o modelo:

```bash
poetry run python src/player_modeling/scripts/generate_raw_events.py --players 200 --seed 42
```

### Simulador / worker publisher (RabbitMQ)

O worker publisher (`src/player_modeling/simulator/`, ADR 0007) simula dois jogadores de teste fixos (`PLAYER_USERNAME_1`, `PLAYER_USERNAME_2`), cada um com uma persona da Taxonomia de Bartle sorteada independentemente a cada ciclo, e publica um lote de 15 a 20 eventos recentes de cada um em uma fila RabbitMQ (fila única, exchange default). Ele roda em loop contínuo — publica um ciclo (uma mensagem por jogador), aguarda `PUBLISHER_INTERVAL_SECONDS` e repete, até ser interrompido (`Ctrl+C`) — para permitir observar como o perfil previsto de um jogador evoluiria ao longo do tempo e testar isolamento de dados entre os dois jogadores. O worker subscriber que consome da fila e persiste no banco ainda não está implementado.

Subir o RabbitMQ localmente (imagem `rabbitmq:3-management`, painel web em `http://localhost:15672`), com credenciais lidas do `.env` (ver `.env.example`, seção "RabbitMQ"):

```bash
docker compose up -d    # ou: make rabbitmq-up
```

Antes de rodar o publisher, defina em `.env` os dois jogadores de teste (ex.: criados via `POST /auth/register`) e o intervalo entre ciclos — ver `.env.example`, seção "Worker publisher": `PLAYER_USERNAME_1`, `PLAYER_USERNAME_2`, `PUBLISHER_INTERVAL_SECONDS`.

Executar o publisher (roda em primeiro plano, publicando ciclos até `Ctrl+C`):

```bash
PYTHONPATH=src poetry run python -m player_modeling.simulator.publisher    # ou: make publisher
```

### Migrações do banco de dados

O schema do SQLite (`db.sqlite3`) é gerenciado por migrações versionadas com Alembic (ADR 0006) em `src/alembic/` (configuração em `alembic.ini` na raiz), não mais criado automaticamente pela API. Aplicar o schema mais recente:

```bash
poetry run alembic upgrade head
```

Para um `db.sqlite3` já existente de uma versão anterior do projeto (tabela `users` criada pela API automaticamente), marcar como já estando na revisão inicial em vez de recriar a tabela:

```bash
poetry run alembic stamp head
```

Reverter a última migração aplicada:

```bash
poetry run alembic downgrade -1
```

### Executar a API e Autenticação

Executar o servidor de desenvolvimento da API FastAPI (com reload):

```bash
poetry run uvicorn player_modeling.api.app:app --reload --port 8000
```

Rotas da API:
* `POST /auth/register`: Registro de usuário na tabela `users` do `db.sqlite3` com hash bcrypt.
* `POST /auth/login`: Autenticação e emissão de Bearer Token JWT.
* `GET /auth/me`: Rota protegida por Bearer Token.
* `GET /players/{player_id}/persona`: Rota protegida por Bearer Token retornando perfil na Taxonomia de Bartle (stub/mock determinístico).

Caso a estrutura de execução seja alterada durante o desenvolvimento, atualizar este arquivo e o README.md.

---

## Convenções de código

### Linguagem

O projeto utiliza **Python 3.13**.

### Estilo

Seguir PEP 8 e priorizar código:

* simples;
* legível;
* modular;
* testável;
* com responsabilidades bem definidas.

### Tipagem

Utilizar type hints nas funções e métodos.

Exemplo:

```python
def calculate_playtime(events: list[dict]) -> float:
    ...
```

### Comentários

Evitar comentários gigantes ou no meio do código.
A regra é que os comentários de uma classe, função ou método estejam na docstring com o seguinte formato:

```python
def sum_values(a: int, b: int) -> int:
      """Sum two integers then return it.

      :param a: The first value to the operation.
      :param b: The second value to sum with first.

      :return: the result of a + b.
      """
      return a + b
```

### Nomenclatura

Utilizar:

* `snake_case` para funções e variáveis;
* `PascalCase` para classes;
* `UPPER_CASE` para constantes;
* nomes descritivos relacionados ao domínio de Player Modeling.

Exemplo:

```python
player_id
session_count
playtime_hours
items_collected
```

### Organização

Organizar o código preferencialmente por **domínio ou funcionalidade**, e não apenas por tipo técnico.

Exemplo:

`src/` agrupa tudo o que é relacionado à implementação do backend: código de domínio, dados de origem e testes. `scripts/`, na raiz do projeto, contém apenas as ferramentas de harness (validação de branch, commit, arquivos sensíveis, diff de escopo) — não faz parte do backend.

```text
src/
├── player_modeling/
│   ├── simulator/    # gera e publica eventos sintéticos no RabbitMQ (cronjob)
│   ├── worker/       # consome, transforma e persiste eventos - ETL (cronjob)
│   ├── ml/           # treinamento e inferência do modelo de perfil (Bartle)
│   ├── api/          # endpoint GET de consulta do perfil do jogador
│   └── scripts/      # scripts executáveis da pipeline/backend (ex.: geração do dataset sintético)
├── alembic/          # migrações versionadas do schema do banco (ADR 0006; config em alembic.ini na raiz)
├── data/             # dataset sintético usado para pré-treinar o modelo (dados de origem)
└── tests/            # testes automatizados (espelham a estrutura de player_modeling/)
```

Os módulos `simulator/`, `worker/`, `ml/` e `api/` ainda não possuem implementação de negócio (apenas `__init__.py` documentando o propósito de cada um); serão preenchidos incrementalmente conforme a pipeline for implementada.

### Dados

O diretório `src/data/` contém o dataset sintético usado para pré-treinar o modelo de ML antes do pipeline real (simulador → RabbitMQ → worker) estar pronto:

* `src/data/events.csv`: eventos brutos sintéticos, no formato que o worker consumiria da fila;
* `src/data/sessions_features.csv`: features agregadas por sessão, já rotuladas com `true_persona`, usadas para treinar o classificador.

Esses arquivos são gerados por `src/player_modeling/scripts/generate_raw_events.py` e não devem ser editados manualmente.

Quando o pipeline real estiver implementado, os eventos publicados pelo simulador e consumidos pelo worker devem ser persistidos em banco de dados, não em arquivos.

### Testes

Toda funcionalidade relevante deve possuir testes automatizados.

Os testes devem estar dentro de `src/tests/`, espelhando o caminho do módulo que verificam: cada teste fica no subdiretório de `src/tests/` correspondente ao diretório do código testado, com o arquivo prefixado por `test_`. Fixtures e configuração compartilhadas (ex.: `conftest.py`) ficam no nível mais alto de `src/tests/` que precisar alcançá-las, aproveitando a propagação automática de `conftest.py` do pytest para os subdiretórios — sem duplicação.

Exemplo do estado atual do repositório:

```text
src/tests/
├── conftest.py              # compartilhado, disponibiliza scripts/ via sys.path
└── scripts/                 # espelha scripts/ (raiz) — só harness tem testes hoje
    ├── test_block_git_push_hook.py   # testa scripts/block_git_push_hook.py
    ├── test_check_branch.py          # testa scripts/check_branch.py
    ├── test_check_commit_message.py  # testa scripts/check_commit_message.py
    ├── test_check_sensitive_paths.py # testa scripts/check_sensitive_paths.py
    └── test_report_scope_diff.py     # testa scripts/report_scope_diff.py
```

A mesma convenção se aplica quando os módulos de `src/player_modeling/` (`api`, `ml`, `simulator`, `worker`, `scripts`) ganharem testes reais (ex.: um teste de `src/player_modeling/ml/model.py` deverá ficar em `src/tests/player_modeling/ml/test_model.py`). Não criar diretórios de teste vazios ou especulativos para módulos que ainda não têm código de negócio implementado.

Preferir testes unitários para funções de transformação e geração de features.

### Documentação

Alterações arquiteturais relevantes devem ser registradas em:

```text
docs/adr/
```

Decisões importantes devem ser documentadas por meio de Architecture Decision Records (ADR).

---

## Não fazer

### Não implementar funcionalidades futuras sem solicitação

O escopo atual já inclui simulador, worker/ETL, RabbitMQ, banco de dados, modelo de ML de classificação Bartle e um endpoint GET de consulta (ver `docs/escopo.md` e "Objetivo inicial" acima).

Não implementar automaticamente, além desse escopo:

* frontend ou qualquer interface visual;
* autenticação e autorização;
* endpoints além do GET de consulta de perfil;
* integração com PlayFab;
* integração com Databricks;
* Redis;
* infraestrutura de produção;
* deploy;
* técnicas de explicabilidade e análise de importância de features;

se essas funcionalidades ainda não fizerem parte da atividade atual.

### Não utilizar dados reais de jogadores

Durante a fase inicial, utilizar **dados sintéticos**.

Não incluir informações pessoais, identificáveis ou sensíveis de jogadores.

### Não modificar dados brutos

Os arquivos `src/data/events.csv` e `src/data/sessions_features.csv` são o dataset sintético usado para pré-treinar o modelo de ML e devem ser tratados como dados de origem: não devem ser editados manualmente nem sobrescritos pelo pipeline. Para regenerá-los, usar sempre `src/player_modeling/scripts/generate_raw_events.py`.

### Não gerar código sem considerar a arquitetura existente

Antes de criar ou modificar código:

1. analisar a estrutura atual do projeto;
2. verificar arquivos relacionados;
3. respeitar as convenções deste documento;
4. verificar testes existentes;
5. evitar duplicação de funcionalidades.

### Não adicionar dependências desnecessárias

Antes de adicionar uma biblioteca, avaliar se a funcionalidade pode ser implementada utilizando as dependências existentes.

Quando uma nova dependência for necessária, explicar sua finalidade.

### Não ignorar testes

Não considerar uma funcionalidade concluída sem verificar se os testes existentes continuam passando.

### Não substituir decisões do desenvolvedor sem justificativa

A IA deve apresentar alternativas e explicar trade-offs quando houver decisões arquiteturais relevantes.

A decisão final sobre alterações significativas deve permanecer com o desenvolvedor.

---

## Princípios para desenvolvimento assistido por IA

A Inteligência Artificial deve ser utilizada como **assistente de desenvolvimento**, não como substituta da revisão humana.

Ao gerar ou modificar código:

1. compreender o contexto existente;
2. propor a solução;
3. implementar somente após avaliar a abordagem;
4. executar ou propor testes;
5. verificar o resultado;
6. explicar alterações relevantes.

Código gerado por IA deve ser revisado antes de ser considerado parte definitiva do projeto.

O projeto deve priorizar **incrementalidade**, permitindo que novas atividades da disciplina adicionem funcionalidades sem exigir uma reestruturação completa da aplicação.

### Push para o repositório remoto

Um hook técnico do Claude Code (`.claude/settings.json`, ver `docs/adr/0003-harness-desenvolvimento.md`) bloqueia incondicionalmente qualquer tentativa do agente de executar `git push`, mesmo se solicitado explicitamente na conversa. O push para `origin` é sempre uma ação manual do desenvolvedor, após revisão. `git commit` e `git merge` locais pelo agente não são bloqueados.
