# Player Modeling Lab

POC experimental para **Modelagem de Jogadores (Player Modeling)** utilizando Engenharia de Dados e, posteriormente, Machine Learning.

O projeto faz parte da disciplina **PPGTI1101**, do Programa de Pós-Graduação em Tecnologia da Informação (PPgTI/UFRN), e será desenvolvido de forma incremental ao longo da disciplina.

## Objetivo

O objetivo inicial é construir, com o auxílio de IA, um repositório Python responsável por:

1. rodar um **simulador** (cronjob) que gera eventos sintéticos de jogadores e os publica em uma fila **RabbitMQ**;
2. rodar um **worker** (outro cronjob) que consome os eventos da fila, transforma-os e os persiste em um banco de dados (processo de ETL);
3. disponibilizar ao menos um **endpoint GET** que retorna, a partir dos eventos mais recentes de um jogador, o perfil previsto por um modelo de Machine Learning segundo a **Taxonomia de Bartle** (`Killer`, `Achiever`, `Socializer`, `Explorer`).

Esta versão não inclui frontend nem autenticação/autorização.

A ideia é utilizar esse projeto como um laboratório para experimentar técnicas de Engenharia de Dados, Machine Learning e desenvolvimento de software assistido por Inteligência Artificial.

### Pipeline inicial

```text
Simulador (cronjob)
      │
      ▼
   RabbitMQ
      │
      ▼
Worker / ETL (cronjob)
      │
      ▼
Banco de dados
      │
      ▼
Modelo de ML (Taxonomia de Bartle)
      │
      ▼
Endpoint GET (perfil do jogador)
```

## Escopo inicial

A primeira versão do projeto trabalha com dados sintéticos de jogadores, tanto na simulação quanto no pré-treino do modelo.

Os eventos representam ações do jogador durante uma sessão, como:

* movimentação (`move`);
* ataque (`attack`);
* exploração de área (`explore_area`);
* interação social (`chat`, `trade`);
* progressão (`quest_complete`, `quest_fail`, `retry`);
* coleta de itens (`loot`);
* inatividade (`idle`).

Enquanto o pipeline real (simulador → RabbitMQ → worker) não está pronto, o modelo de ML é pré-treinado com um dataset sintético gerado por `scripts/generate_raw_events.py`, que produz:

* `data/events.csv`: eventos brutos, no mesmo formato que o worker consumiria da fila;
* `data/sessions_features.csv`: features agregadas por sessão (percentuais por tipo de evento, tempo médio de decisão, taxa de falha) já rotuladas com o perfil verdadeiro (`true_persona`), usadas para treinar o classificador.

## Evolução planejada

O escopo inicial já cobre simulador, worker/ETL, banco de dados, modelo de ML e endpoint de consulta (ver "Objetivo" acima). Funcionalidades futuras poderão incluir:

1. endpoints adicionais além do GET de consulta de perfil;
2. frontend para visualização dos perfis;
3. autenticação e autorização;
4. análise de importância das features;
5. técnicas de explicabilidade;
6. integração com fontes externas de eventos, como plataformas de jogos reais;
7. experimentos adicionais relacionados à pesquisa de Player Modeling.

Essas funcionalidades **não devem ser implementadas antecipadamente** sem uma solicitação explícita.

## Estrutura do projeto

```text
player-modeling-lab/
│
├── CLAUDE.md
├── README.md
├── requirements.txt
│
├── docs/
│   ├── adr/
│   │   ├── 0001-escolha-da-ferramenta-de-ia.md
│   │   └── 0002-git-flow.md
│   ├── escopo.md
│   └── prompts-comparacao.md
│
├── data/
│   ├── events.csv
│   └── sessions_features.csv
│
├── scripts/
│   └── generate_raw_events.py
│
├── src/
│   └── player_modeling/
│       ├── simulator/
│       ├── worker/
│       ├── ml/
│       └── api/
│
└── tests/
```

### Organização dos diretórios

| Diretório                          | Responsabilidade                                          |
| ----------------------------------- | ---------------------------------------------------------- |
| `src/`                              | Código-fonte da aplicação                                  |
| `src/player_modeling/simulator/`    | Cronjob que gera e publica eventos sintéticos no RabbitMQ  |
| `src/player_modeling/worker/`       | Cronjob que consome, transforma e persiste eventos (ETL)   |
| `src/player_modeling/ml/`           | Treinamento e inferência do modelo de perfil (Bartle)      |
| `src/player_modeling/api/`          | Endpoint GET de consulta do perfil do jogador               |
| `scripts/`                          | Scripts utilitários, como o gerador do dataset sintético   |
| `data/`                             | Dataset sintético usado para pré-treinar o modelo de ML     |
| `tests/`                            | Testes automatizados                                       |
| `docs/adr/`                         | Architecture Decision Records                               |
| `docs/`                             | Documentação complementar                                    |

## Tecnologias

A versão inicial utiliza:

* **Python 3.13**
* **RabbitMQ** (fila de mensagens entre simulador e worker)
* um **banco de dados** para persistência dos eventos processados (tecnologia a definir)
* **scikit-learn** (modelo de classificação da Taxonomia de Bartle)
* **Pandas**
* **Pydantic**
* **Pytest**
* **Git**
* **GitHub**

A stack poderá ser ampliada conforme as necessidades das próximas etapas do projeto.

## Instalação

Clone o repositório:

```bash
git clone <URL_DO_REPOSITORIO>
cd ia-dev-lab
```

Instale as dependências com [Poetry](https://python-poetry.org/) (cria automaticamente um virtualenv em `.venv/`, dentro do projeto):

```bash
poetry install
```

Ative os hooks de pré-commit (formatação, lint, verificação de tipos e testes rápidos rodam antes de cada commit):

```bash
poetry run pre-commit install
```

## Executando os testes

Execute todos os testes com:

```bash
poetry run pytest
```

Para executar um arquivo de teste específico:

```bash
poetry run pytest tests/test_nome_do_teste.py
```

Para rodar manualmente as mesmas verificações do harness (lint, formatação e tipos):

```bash
poetry run ruff check .
poetry run ruff format .
poetry run mypy .
```

Antes de considerar uma tarefa concluída, rode o relatório de escopo para conferir se as alterações estão restritas ao esperado (a branch base padrão é `dev`):

```bash
poetry run python scripts/report_scope_diff.py [branch-base]
```

O comando lista os arquivos alterados em relação à branch base e sinaliza alterações em `data/events.csv` ou `data/sessions_features.csv`, que nunca devem ser editados manualmente.

## Executando o pipeline

O pipeline terá três pontos de entrada: o simulador (cronjob), o worker/ETL (cronjob) e a API (endpoint GET de consulta de perfil). Os comandos específicos de cada um serão definidos durante a implementação e documentados aqui e no `CLAUDE.md`.

Enquanto isso, o dataset sintético usado para pré-treinar o modelo pode ser gerado com:

```bash
poetry run python scripts/generate_raw_events.py --players 200 --seed 42
```

## Dados

A versão inicial utiliza **dados sintéticos**.

Enquanto o pipeline real (simulador → RabbitMQ → worker) não está pronto, o modelo de ML é pré-treinado com o dataset gerado por `scripts/generate_raw_events.py`:

```text
data/events.csv             # eventos brutos sintéticos
data/sessions_features.csv  # features agregadas por sessão, rotuladas com true_persona
```

Esses arquivos não devem ser editados manualmente nem sobrescritos pelo pipeline; para regerá-los, execute novamente o script gerador.

Quando o pipeline real estiver implementado, os eventos publicados pelo simulador e consumidos pelo worker devem ser persistidos em banco de dados, não em arquivos.

## Desenvolvimento assistido por IA

A Inteligência Artificial é utilizada como ferramenta de apoio ao desenvolvimento do projeto.

Entre as atividades realizadas com auxílio de IA estão:

* geração e revisão de código;
* criação de testes;
* análise de arquitetura;
* documentação;
* refatoração;
* análise de dados;
* geração de prompts de desenvolvimento.

Todo código gerado ou modificado com auxílio de IA deve passar por revisão humana antes de ser incorporado ao projeto.

Um hook técnico do Claude Code (`.claude/settings.json`, ver `docs/adr/0003-harness-desenvolvimento.md`) bloqueia incondicionalmente qualquer tentativa do agente de IA de executar `git push` — inclusive se solicitado na conversa. O push para o repositório remoto é sempre uma ação manual do desenvolvedor, após revisão. `git commit` e `git merge` locais pelo agente não são afetados por esse bloqueio.

As regras e o contexto para desenvolvimento assistido por IA estão documentados em [`CLAUDE.md`](./CLAUDE.md).
