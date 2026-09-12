## 1. Dependências

- [x] 1.1 Adicionar `pandas` e `scikit-learn` ao grupo principal de `[tool.poetry.dependencies]` em `pyproject.toml` (decisão 8 do `design.md`) e verificar que `poetry install` conclui sem erro e que `poetry run python -c "import pandas, sklearn"` executa com sucesso.

## 2. Módulo de ML (`ml/knn.py`)

- [x] 2.1 Reescrever `src/player_modeling/ml/knn.py` como biblioteca sem efeito colateral no import: constante com o caminho de `src/data/sessions_features.csv` resolvido a partir de `Path(__file__)` (independente do `cwd`), constante com a tupla ordenada das colunas de feature (`n_events`, `pct_attack`, `pct_explore`, `pct_social`, `pct_quest_complete`, `pct_retry`, `avg_decision_time_ms`, `fail_rate`) e da coluna-rótulo (`true_persona`), sem `print`, sem `exit()` e sem código de treino em nível de módulo — verificar que `poetry run python -c "import player_modeling.ml.knn"` não produz saída nem lê o CSV.
- [x] 2.2 Implementar a função de treino que carrega o dataset completo, ajusta `StandardScaler` + `LabelEncoder` + `KNeighborsClassifier(n_neighbors=5)` e devolve uma dataclass `frozen` com os artefatos de inferência e a ordem das colunas (decisões 2 e 3 do `design.md`), verificando via teste que os artefatos devolvidos estão ajustados e que as classes do encoder são exatamente os quatro rótulos da Taxonomia de Bartle.
- [x] 2.3 Implementar a função de predição que recebe os artefatos treinados e um dicionário de features no formato de `player_features`/`worker.features.extract_features`, valida estritamente o conjunto de features (erro explícito para feature faltante ou desconhecida), aplica o scaler na ordem de treino e devolve `BartlePersona` (decisões 4 e 7 do `design.md`) — verificar por teste de sucesso e por teste de falha com feature faltando/extra.
- [x] 2.4 Implementar a função separada de avaliação (`train_test_split` estratificado + acurácia/relatório) usada por testes e análise, fora do caminho de startup e sem `print` (decisão 3 do `design.md`), verificando por teste que a acurácia retornada está no intervalo `[0.0, 1.0]` e acima de um limiar mínimo razoável para o dataset sintético.
- [x] 2.5 Atualizar a docstring de `src/player_modeling/ml/__init__.py` para descrever o módulo implementado (remover "ainda não implementado"), verificando o texto com `git diff`.

## 3. Treino no startup da API

- [x] 3.1 Treinar o classificador uma única vez no `lifespan` de `src/player_modeling/api/app.py` e guardar os artefatos em `app.state` (decisões 1 e 2 do `design.md`), verificando por teste que subir a aplicação com `TestClient` disponibiliza os artefatos treinados em `app.state`.
- [x] 3.2 Criar a dependency de acesso ao classificador treinado a partir de `app.state` para uso nas rotas, verificando por teste que a dependency devolve o mesmo objeto treinado entre duas requisições (modelo não é retreinado por requisição).

## 4. Endpoint de consulta do perfil

- [x] 4.1 Implementar em `src/player_modeling/api/routes/players.py` a leitura da linha mais recente de `player_features` do jogador (`WHERE player_id = ? ORDER BY id DESC LIMIT 1`, decisão 6 do `design.md`), verificando por teste que, com histórico de várias linhas, a função devolve a última inserida e `None` quando não há linha.
- [x] 4.2 Substituir `GET /players/{player_id}/persona` por `GET /players/me/persona` (decisão 5 do `design.md`): jogador obtido do `username` do usuário autenticado via `Depends(get_current_user)`, features da linha mais recente, persona prevista pelo classificador em `app.state` e resposta em `PersonaResponse`; verificar por teste de integração o `200 OK` com persona pertencente ao Enum `BartlePersona`.
- [x] 4.3 Responder `404 Not Found` com mensagem explícita quando o jogador autenticado não tiver nenhuma linha em `player_features`, verificando por teste de integração com usuário registrado e tabela vazia.
- [x] 4.4 Remover o stub `resolve_mock_persona` e a lista de personas mockadas de `src/player_modeling/api/routes/players.py`, verificando com `grep -rn "resolve_mock_persona" src/` que não há mais referências no código nem nos testes.

## 5. Testes automatizados

- [x] 5.1 Criar `src/tests/player_modeling/ml/test_knn.py` cobrindo treino, predição, validação estrita de features e avaliação do módulo `ml.knn` sobre o dataset real de `src/data/sessions_features.csv`, verificando aprovação com `poetry run pytest src/tests/player_modeling/ml/test_knn.py`.
- [x] 5.2 Adicionar em `src/tests/player_modeling/ml/test_knn.py` um teste de compatibilidade que confirme que as features produzidas por `player_modeling.worker.features.extract_features` (excluindo `session_id`/`player_id`) correspondem exatamente ao conjunto de features esperado pelo classificador (requisito de compatibilidade do `spec.md`).
- [x] 5.3 Reescrever `src/tests/player_modeling/api/test_persona.py` para o novo contrato: fixture que aplica as migrações e popula `users` e `player_features`, cenários de `200 OK` (persona no Enum), uso da linha mais recente quando há histórico, `404` sem features, `401` sem token / com token inválido / com token expirado, e isolamento entre dois jogadores distintos; remover os cenários do stub e do `422` de formato de `player_id`, verificando aprovação com `poetry run pytest src/tests/player_modeling/api/test_persona.py`.
- [x] 5.4 Executar a suíte completa com `poetry run pytest` e confirmar que nenhum teste existente (incluindo `test_schemas.py` e os testes de rotas protegidas) quebrou com a mudança de contrato.

## 6. Qualidade, documentação e governança

- [x] 6.1 Rodar `poetry run ruff check .`, `poetry run ruff format .` e `poetry run mypy .` e corrigir apontamentos até obter aprovação completa, preservando `disallow_untyped_defs` nas funções novas.
- [x] 6.2 Atualizar `README.md` e `CLAUDE.md` documentando a nova rota `GET /players/me/persona`, o treino do KNN no startup (`make run`) e as novas dependências, removendo as descrições de "stub/mock determinístico", e verificar o resultado com `git diff`.
- [x] 6.3 Criar `docs/adr/0010-*.md` registrando o classificador KNN, o treino em memória no startup (trade-off contra modelo serializado) e a derivação do jogador a partir do usuário autenticado (decisão 9 do `design.md`), verificando que a ADR referencia as ADRs 0005, 0007 e 0008.
- [x] 6.4 Executar `poetry run python scripts/report_scope_diff.py dev` e confirmar que não há alterações fora do escopo (em especial nenhuma alteração em `src/data/` ou em migrações Alembic).
