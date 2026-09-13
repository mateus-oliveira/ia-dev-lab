## Why

O endpoint `GET /players/me/persona` (ADR 0010) serve a predição de **um único** modelo, um KNN
treinado no startup da API. Isso basta para fechar o item 3 do objetivo inicial da POC, mas deixa
sem resposta a pergunta que um laboratório de Player Modeling precisa fazer: *este perfil é uma
propriedade do jogador ou um artefato do algoritmo escolhido?* Com um modelo só, não há como
distinguir as duas coisas nem observar onde os modelos discordam.

Uma Árvore de Decisão é o contraponto natural ao KNN para esse fim: aprende regras por limiar em
cada feature (`pct_attack > 0.4`, `avg_decision_time_ms < 800`) em vez de vizinhança no espaço
normalizado, e portanto erra em situações diferentes. Divergência entre os dois é sinal de
fronteira ambígua entre personas — informação de domínio que hoje o projeto descarta.

Há também uma motivação estrutural: `ml/knn.py` concentra hoje, em um único módulo, três
responsabilidades distintas — o **contrato de dados** (caminho do dataset, colunas de feature,
coluna-rótulo), o **pipeline de treino/avaliação/inferência** (carga, `LabelEncoder`,
`StandardScaler`, `train_test_split`, métricas) e a **escolha do estimador** (`KNeighborsClassifier`
com `n_neighbors=5`). Adicionar um segundo modelo por cópia duplicaria as duas primeiras para
variar apenas a terceira.

## What Changes

- **Núcleo compartilhado (`src/player_modeling/ml/persona_model.py`)**: novo módulo com tudo que
  não depende do algoritmo — constantes do dataset e das features, as dataclasses
  `PersonaClassifier` e `ClassifierEvaluation`, `load_dataset`, e as funções de treino, predição e
  avaliação parametrizadas pelo estimador scikit-learn recebido como argumento.
- **`ml/knn.py` reduzido à sua especificidade**: mantém o hiperparâmetro `N_NEIGHBORS` e passa a
  expor `train_classifier`/`evaluate_classifier` como camadas finas sobre o núcleo, sem duplicar
  carga de dataset, encoding, escalonamento nem cálculo de métricas.
- **Novo `ml/decision_tree.py`**: espelha a interface pública de `ml/knn.py`
  (`train_classifier`, `evaluate_classifier`, `build_estimator`) com um
  `DecisionTreeClassifier` e seus próprios hiperparâmetros (`MAX_DEPTH`, `RANDOM_STATE`).
- **Dois modelos treinados no startup**: o `lifespan` da API treina os dois classificadores uma
  única vez e os guarda em `app.state.persona_classifiers`, um dicionário indexado pela chave do
  modelo (`knn`, `decision_tree`). Nenhuma requisição retreina nada; a inferência por requisição
  passa a rodar os dois modelos sobre a mesma linha de features.
- **BREAKING — contrato de resposta do endpoint**: `PersonaResponse` deixa de ter o campo
  `persona` e passa a ter um campo por modelo, nomeado pela chave do modelo:
  `{"player_id": "player_0001", "knn": "Killer", "decision_tree": "Explorer"}`. Decisão tomada
  pelo desenvolvedor no checkpoint humano da atividade (ver `docs/aula6/etapa3-checkpoint.md`),
  em cima de uma proposta diferente feita pelo agente.
- **`evaluate_model.py` passa a avaliar os dois modelos**: ganha `--model knn|decision-tree|both`
  (padrão `both`), para comparar acurácia e relatório por classe lado a lado.
- **Documentação**: `README.md` e `CLAUDE.md` descrevem o novo contrato e os dois modelos; nova
  ADR registra a extração do núcleo compartilhado e a escolha da Árvore de Decisão.
- **Fora de escopo** (seção "Não fazer" do `CLAUDE.md`): análise de importância das features da
  árvore e qualquer forma de explicabilidade (embora a árvore torne isso trivial, é explicitamente
  uma evolução futura); persistir modelos em disco; endpoints adicionais; votação/ensemble entre os
  modelos; qualquer alteração no simulador, no worker, no schema de `player_features` ou nos CSVs
  de `src/data/`.

## Capabilities

### Modified Capabilities
- `player-persona-inference`: a resposta passa a conter a predição de **cada** modelo disponível,
  identificada pelo nome do modelo, em vez de uma única persona sem atribuição de origem.

### New Capabilities
(nenhuma — a capacidade de inferência já existe e está sendo alterada.)

## Impact

- **Código**: novo `src/player_modeling/ml/persona_model.py`; novo `src/player_modeling/ml/decision_tree.py`;
  `src/player_modeling/ml/knn.py` reduzido; `src/player_modeling/api/app.py` (treino dos dois
  modelos no `lifespan`); `src/player_modeling/api/routes/players.py` (predição dupla);
  `src/player_modeling/api/schemas.py` (`PersonaResponse`); `src/player_modeling/scripts/evaluate_model.py`.
- **API**: alteração incompatível no corpo de resposta de sucesso. Os códigos `401` e `404` e a
  regra de derivar o jogador do token permanecem inalterados.
- **Dados**: nenhuma alteração — leitura somente-leitura do dataset e de `player_features`, sem
  migração Alembic.
- **Dependências**: nenhuma nova (`DecisionTreeClassifier` já vem com `scikit-learn`).
- **Testes**: novo `src/tests/player_modeling/ml/test_decision_tree.py` e
  `src/tests/player_modeling/ml/test_persona_model.py`; ajuste de
  `src/tests/player_modeling/ml/test_knn.py` e `src/tests/player_modeling/api/test_persona.py`
  para o novo contrato.
- **Startup da API**: passa a treinar dois modelos em vez de um (impacto pequeno; a árvore treina
  mais rápido que o KNN sobre 1000 linhas).
