## Why

O item 3 do objetivo inicial da POC (`CLAUDE.md`; item 3 de "Uso de SDD antes da implementação da pipeline" em `docs/escopo.md`, que prevê a pipeline em `src/` especificada por SDD) exige um endpoint GET que, **a partir dos eventos mais recentes de um jogador**, retorne o perfil previsto por um **modelo de Machine Learning** segundo a Taxonomia de Bartle. Hoje o endpoint `GET /players/{player_id}/persona` cumpre apenas o contrato HTTP: responde com um stub determinístico (`resolve_mock_persona`), ignora o usuário autenticado e não consulta dado algum — nem o histórico de features que o worker subscriber (ADR 0008) já persiste em `player_features`.

Com o publisher (ADR 0007), o worker/ETL (ADR 0008) e o dataset sintético rotulado (`src/data/sessions_features.csv`) prontos, as duas pontas que faltavam para fechar o fluxo existem: há dados reais de features por jogador no banco e há dados rotulados para treinar o classificador. Esta change substitui o stub por inferência real com um classificador KNN e passa a derivar o jogador consultado do usuário autenticado, em vez de aceitá-lo como parâmetro de rota.

## What Changes

- **Módulo de ML treinável (`src/player_modeling/ml/knn.py`)**: o script de treino exploratório existente (feito em notebook, com `PATH` placeholder, `print`s e `exit()` em nível de módulo) passa a ser um módulo de biblioteca importável sem efeitos colaterais, expondo uma função de treino (que devolve os artefatos de inferência: modelo KNN, `StandardScaler`, `LabelEncoder` e a ordem das colunas de feature) e uma função de predição que recebe um dicionário de features e devolve a persona da Taxonomia de Bartle. O caminho do dataset passa a ser resolvido a partir da localização do próprio módulo, independente do diretório de trabalho.
- **Treino único na subida da API (`make run`)**: o `lifespan` do FastAPI treina o classificador uma vez no startup e guarda os artefatos treinados em `app.state`, consumidos pelo endpoint via dependency. Nenhuma requisição treina o modelo.
- **BREAKING — endpoint de persona sem `player_id` no path**: `GET /players/{player_id}/persona` é substituído por uma rota sem parâmetro de jogador (`GET /players/me/persona`), que obtém o `player_id` exclusivamente do `username` do usuário autenticado (Bearer Token JWT, ADR 0005). Clientes que hoje montam a URL com um `player_id` arbitrário precisam ser ajustados, e um usuário deixa de poder consultar o perfil de outro jogador.
- **Inferência a partir de dados reais**: o endpoint busca a linha mais recente de `player_features` do jogador autenticado (aproveitando o índice composto `(player_id, id)` criado na ADR 0008), monta o vetor de features na mesma ordem do treino e retorna a persona prevista pelo KNN em `PersonaResponse`.
- **Erro explícito na ausência de dados**: quando o jogador autenticado ainda não possui nenhuma linha em `player_features` (pipeline não processou eventos dele), a API responde `404 Not Found` em vez de devolver uma persona inventada.
- **Remoção do stub**: `resolve_mock_persona` e a lista `_BARTLE_PERSONAS` de mock são removidos de `src/player_modeling/api/routes/players.py`, junto com os testes que validavam o comportamento mockado e a validação de formato do path param (`422`), que deixa de existir.
- **Novas dependências de runtime**: `pandas` e `scikit-learn` passam ao grupo principal do `pyproject.toml` — são usadas pela API em execução, não só em desenvolvimento.
- **Documentação**: `README.md` e `CLAUDE.md` deixam de descrever o endpoint como "stub/mock determinístico"; uma nova ADR (0010) registra as decisões de treinar no startup (em vez de versionar um modelo serializado) e de derivar o jogador do usuário autenticado.
- **Fora de escopo** (seção "Não fazer" do `CLAUDE.md`): persistir o modelo treinado em disco (`.pkl`/`joblib`); endpoints adicionais além do GET de consulta de perfil; frontend; novos mecanismos de autenticação/autorização; explicabilidade e análise de importância de features; alterações no simulador, no worker ou no schema de `player_features`; qualquer reescrita de `generate_raw_events.py` ou dos CSVs de `src/data/` (dados de origem — não editar).

## Capabilities

### New Capabilities
- `player-persona-inference`: predição da persona (Taxonomia de Bartle) do jogador autenticado a partir da linha mais recente de `player_features`, usando um classificador KNN treinado no startup da API com o dataset sintético rotulado. Supersede a capacidade `inference-endpoint` da change arquivada `2026-09-11-inference-endpoint` (stub/mock), que nunca foi sincronizada para `openspec/specs/` e portanto não admite um delta — o comportamento mockado que ela especificava deixa de valer.

### Modified Capabilities
<!-- Nenhuma capacidade existente em openspec/specs/ tem requisitos alterados. -->

## Impact

- **Código**: `src/player_modeling/ml/knn.py` (reescrito como biblioteca) e `src/player_modeling/ml/__init__.py` (docstring deixa de dizer "ainda não implementado"); `src/player_modeling/api/app.py` (treino no `lifespan` + `app.state`); `src/player_modeling/api/routes/players.py` (nova rota, consulta a `player_features`, remoção do stub).
- **API**: alteração incompatível no contrato da rota de persona (path sem `player_id`); novo código de erro `404`; `401` de autenticação preservado; `422` de formato de `player_id` deixa de existir.
- **Dados**: leitura somente-leitura de `src/data/sessions_features.csv` no startup e leitura da tabela `player_features`; nenhuma escrita em dados de origem e nenhuma alteração de schema (sem nova migração Alembic).
- **Dependências**: `pandas` e `scikit-learn` adicionados ao grupo principal do `pyproject.toml` (impacto no tempo de `poetry install` e no tempo de subida da API, que passa a treinar o modelo).
- **Testes**: novo `src/tests/player_modeling/ml/test_knn.py`; reescrita de `src/tests/player_modeling/api/test_persona.py` (fixture passa a popular `player_features`); ajuste de eventuais referências a `resolve_mock_persona` em outros testes.
- **Documentação/governança**: `README.md`, `CLAUDE.md` e nova ADR 0010; tipagem estrita (`disallow_untyped_defs`) e Ruff mantidos.
