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

Enquanto o pipeline real (simulador → RabbitMQ → worker) não está pronto, o modelo de ML é pré-treinado com o dataset sintético gerado por `scripts/generate_raw_events.py` (`data/events.csv` e `data/sessions_features.csv`, este último já rotulado com `true_persona` para treino supervisionado).

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
poetry run pytest tests/test_nome_do_teste.py
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

O pipeline terá três pontos de entrada: simulador (cronjob), worker/ETL (cronjob) e API (endpoint GET). Os comandos específicos de cada um serão definidos durante a implementação.

Gerar o dataset sintético usado para pré-treinar o modelo:

```bash
poetry run python scripts/generate_raw_events.py --players 200 --seed 42
```

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

```text
src/
└── player_modeling/
    ├── simulator/    # gera e publica eventos sintéticos no RabbitMQ (cronjob)
    ├── worker/       # consome, transforma e persiste eventos - ETL (cronjob)
    ├── ml/           # treinamento e inferência do modelo de perfil (Bartle)
    └── api/          # endpoint GET de consulta do perfil do jogador
```

### Dados

O diretório `data/` contém o dataset sintético usado para pré-treinar o modelo de ML antes do pipeline real (simulador → RabbitMQ → worker) estar pronto:

* `data/events.csv`: eventos brutos sintéticos, no formato que o worker consumiria da fila;
* `data/sessions_features.csv`: features agregadas por sessão, já rotuladas com `true_persona`, usadas para treinar o classificador.

Esses arquivos são gerados por `scripts/generate_raw_events.py` e não devem ser editados manualmente.

Quando o pipeline real estiver implementado, os eventos publicados pelo simulador e consumidos pelo worker devem ser persistidos em banco de dados, não em arquivos.

### Testes

Toda funcionalidade relevante deve possuir testes automatizados.

Os testes devem estar dentro de:

```text
tests/
```

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

Os arquivos `data/events.csv` e `data/sessions_features.csv` são o dataset sintético usado para pré-treinar o modelo de ML e devem ser tratados como dados de origem: não devem ser editados manualmente nem sobrescritos pelo pipeline. Para regenerá-los, usar sempre `scripts/generate_raw_events.py`.

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
