## 1. RED — testes antes da implementação

- [x] 1.1 Criar `src/tests/player_modeling/ml/test_decision_tree.py` descrevendo o comportamento esperado do novo modelo (treino devolve artefatos ajustados; classes do encoder são exatamente as quatro personas de Bartle; predição devolve `BartlePersona`; features faltando ou desconhecidas levantam erro; acurácia acima de um limiar mínimo), e confirmar com `poetry run pytest src/tests/player_modeling/ml/test_decision_tree.py` que **todos falham** por ausência de implementação.
- [x] 1.2 Atualizar `src/tests/player_modeling/api/test_persona.py` para o contrato aprovado no checkpoint (`player_id`, `knn`, `decision_tree`; ausência do campo `persona`) e confirmar que os cenários do novo contrato falham, enquanto `401` e `404` continuam passando.
- [x] 1.3 Registrar a saída do pytest em vermelho como evidência da Etapa 2 em `docs/aula6/etapa2-tdd.md`.

## 2. GREEN — implementação mínima que torna os testes verdes

- [x] 2.1 Implementar `src/player_modeling/ml/decision_tree.py` com `MODEL_KEY`, `MAX_DEPTH`, `build_estimator()`, `train_classifier()` e `evaluate_classifier()`, verificando que `poetry run pytest src/tests/player_modeling/ml/test_decision_tree.py` passa inteiro.
- [x] 2.2 Alterar `PersonaResponse` em `src/player_modeling/api/schemas.py` para o contrato aprovado (um campo por modelo, sem `persona`).
- [x] 2.3 Treinar os dois modelos no `lifespan` de `src/player_modeling/api/app.py`, guardando-os em `app.state.persona_classifiers` indexados pela chave do modelo.
- [x] 2.4 Ajustar `src/player_modeling/api/routes/players.py` para ler as features uma única vez e devolver a predição dos dois modelos, verificando com `poetry run pytest src/tests/player_modeling/api/test_persona.py` que o contrato novo passa.

## 3. REFACTOR — extrair o núcleo compartilhado com os testes verdes

- [x] 3.1 Criar `src/player_modeling/ml/persona_model.py` com o contrato de dados (`DATASET_PATH`, `FEATURE_COLUMNS`, `LABEL_COLUMN`, `DEFAULT_TEST_SIZE`, `DEFAULT_RANDOM_STATE`), as dataclasses `PersonaClassifier` e `ClassifierEvaluation`, `load_dataset`, `predict_persona`, `_build_feature_row` e as funções de treino/avaliação parametrizadas pelo estimador.
- [x] 3.2 Reduzir `src/player_modeling/ml/knn.py` e `src/player_modeling/ml/decision_tree.py` a `MODEL_KEY`, hiperparâmetros, `build_estimator()` e camadas finas sobre o núcleo, sem nenhuma lógica de pipeline duplicada — confirmar com `grep -n "StandardScaler\|LabelEncoder\|train_test_split\|read_csv" src/player_modeling/ml/*.py` que essas chamadas existem apenas em `persona_model.py`.
- [x] 3.3 Atualizar os imports de `api/app.py`, `api/routes/players.py` e dos testes para o núcleo compartilhado.
- [x] 3.4 Criar `src/tests/player_modeling/ml/test_persona_model.py` cobrindo o núcleo de forma independente do algoritmo (carga do dataset, erro de dataset ausente, erro de coluna faltante, validação estrita de features, ordem das colunas preservada).
- [x] 3.5 Rodar `poetry run pytest` inteiro após cada passo da refatoração e confirmar que a suíte permanece verde do início ao fim (nenhum teste alterado para acomodar o refactor).

## 4. Script de avaliação

- [x] 4.1 Adicionar `--model knn|decision-tree|both` (padrão `both`) a `src/player_modeling/scripts/evaluate_model.py`, imprimindo acurácia e relatório por modelo, e executar o script para registrar a comparação real entre os dois classificadores.

## 5. Qualidade, documentação e governança

- [x] 5.1 Rodar `poetry run ruff check .`, `poetry run ruff format .` e `poetry run mypy .`, corrigindo apontamentos.
- [x] 5.2 Atualizar `README.md` e `CLAUDE.md` com o novo contrato do endpoint, os dois modelos e a nova opção do script.
- [x] 5.3 Criar a ADR da extração do núcleo compartilhado e da adição da Árvore de Decisão, referenciando a ADR 0010.
- [x] 5.4 Executar `poetry run python scripts/report_scope_diff.py dev` e confirmar que não há alterações em `src/data/` nem em migrações.
