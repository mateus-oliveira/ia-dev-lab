---
description: "Task list for feature 002-espelhar-testes-src"
---

# Tasks: Espelhar src/tests/ pela organização dos módulos verificados

**Input**: Design documents from `/specs/002-espelhar-testes-src/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [quickstart.md](./quickstart.md)

**Tests**: Não solicitados explicitamente na spec — esta feature reorganiza testes existentes, não adiciona testes novos. A verificação é feita rodando a suíte já existente (`poetry run pytest`) e os passos de `quickstart.md`.

**Organization**: Tarefas agrupadas por user story da [spec.md](./spec.md) (US1 e US2 = P1, US3 = P2).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependência de tarefa incompleta)
- **[Story]**: A qual user story pertence (US1, US2, US3)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirmar baseline verde antes de mover qualquer teste.

- [X] T001 Rodar `poetry run pytest -q` a partir da raiz e confirmar 46 testes passando, registrando a contagem como baseline para comparação pós-reorganização

**Checkpoint**: Baseline confirmada.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Criar o diretório de destino antes de mover qualquer arquivo.

- [X] T002 Criar o diretório `src/tests/scripts/` (sem `__init__.py` — pytest não exige para descoberta de testes; consistente com `src/tests/` atual, que também não tem)

**Checkpoint**: Diretório de destino existe — as movimentações podem começar.

---

## Phase 3: User Story 1 - Testes de harness espelham scripts/ (Priority: P1) 🎯 MVP

**Goal**: Mover os cinco testes de harness para `src/tests/scripts/`, espelhando `scripts/`.

**Independent Test**: Revisar a árvore de `src/tests/` e rodar cada teste movido individualmente.

### Implementation for User Story 1

- [X] T003 [P] [US1] Mover `src/tests/test_block_git_push_hook.py` para `src/tests/scripts/test_block_git_push_hook.py` via `git mv`
- [X] T004 [P] [US1] Mover `src/tests/test_check_branch.py` para `src/tests/scripts/test_check_branch.py` via `git mv`
- [X] T005 [P] [US1] Mover `src/tests/test_check_commit_message.py` para `src/tests/scripts/test_check_commit_message.py` via `git mv`
- [X] T006 [P] [US1] Mover `src/tests/test_check_sensitive_paths.py` para `src/tests/scripts/test_check_sensitive_paths.py` via `git mv`
- [X] T007 [P] [US1] Mover `src/tests/test_report_scope_diff.py` para `src/tests/scripts/test_report_scope_diff.py` via `git mv`
- [X] T008 [US1] Confirmar, via `find src/tests -maxdepth 1 -type f`, que só `conftest.py` permanece solto em `src/tests/` (nenhum `test_*.py` restante na raiz da suíte)

**Checkpoint**: Testes de harness movidos e espelhando `scripts/`.

---

## Phase 4: User Story 2 - conftest.py compartilhado continua funcionando (Priority: P1)

**Goal**: Confirmar que `src/tests/conftest.py`, sem ser movido nem duplicado, continua disponibilizando os scripts de harness via `sys.path` para os testes agora em `src/tests/scripts/`.

**Independent Test**: Rodar a suíte completa e cada teste individualmente, confirmando ausência de `ModuleNotFoundError`.

### Implementation for User Story 2

- [X] T009 [US2] Confirmar que `src/tests/conftest.py` não foi movido nem duplicado (depende de T003-T007)
- [X] T010 [US2] Rodar `poetry run pytest -q` e confirmar 46 testes passando, sem erro de import (depende de T003-T008)
- [X] T011 [P] [US2] Rodar cada teste de harness individualmente (`poetry run pytest src/tests/scripts/test_check_branch.py -v`, etc.) e confirmar que cada um importa corretamente o script correspondente

**Checkpoint**: User Stories 1 e 2 completas — testes movidos e funcionando via `conftest.py` compartilhado.

---

## Phase 5: User Story 3 - Convenção documentada para módulos futuros (Priority: P2)

**Goal**: Documentar a regra de espelhamento no `CLAUDE.md`, sem criar estrutura especulativa para `src/player_modeling/*`.

**Independent Test**: Revisar a seção "Testes" do `CLAUDE.md`.

### Implementation for User Story 3

- [X] T012 [US3] Atualizar a seção "Testes" do `CLAUDE.md`: descrever a regra genérica de espelhamento (cada teste no caminho de `src/tests/` correspondente ao módulo verificado) com o exemplo atual (`src/tests/scripts/test_check_branch.py` ↔ `scripts/check_branch.py`), e observar que módulos de `src/player_modeling/*` seguirão a mesma convenção quando ganharem testes reais
- [X] T013 [US3] Buscar e atualizar eventuais referências a caminhos antigos de teste em `README.md` (`grep -n "tests/test_" README.md`)
- [X] T014 [US3] Confirmar que nenhum diretório vazio foi criado sob `src/tests/` para `player_modeling/{api,ml,simulator,worker,scripts}` (`find src/tests -maxdepth 1 -type d`)

**Checkpoint**: Todas as user stories completas — testes reorganizados, funcionando, e convenção documentada.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validação final.

- [X] T015 Rodar `poetry run ruff check .`, `poetry run ruff format --check .` e `poetry run mypy .` e confirmar que todos passam (quickstart.md passo 4)
- [X] T016 Rodar `poetry run pre-commit run --all-files` e confirmar que passa sem falhas relacionadas à reorganização (quickstart.md passo 5)
- [X] T017 [P] Rodar `poetry run python scripts/report_scope_diff.py` (branch base a definir pelo desenvolvedor, ex.: `dev` ou `refactor/with-gh-spec-kit`) e revisar a lista de arquivos alterados
- [X] T018 Revisar `git status`/`git diff` final e confirmar que nenhum `__pycache__` ou artefato gerado foi versionado acidentalmente

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências.
- **Foundational (Phase 2)**: Depende do Setup — bloqueia as movimentações da US1.
- **US1 (Phase 3)**: Depende do Foundational (diretório de destino deve existir).
- **US2 (Phase 4)**: Depende da conclusão de US1 (T003-T008) — precisa que os arquivos já estejam no novo caminho para validar o `conftest.py`.
- **US3 (Phase 5)**: Independente de US1/US2 na criação do texto, mas documenta o resultado delas — melhor fazer por último para descrever o estado final real.
- **Polish (Phase 6)**: Depende de todas as user stories completas.

### Parallel Opportunities

- T003, T004, T005, T006, T007 podem rodar em paralelo (arquivos diferentes).
- T011 pode rodar em paralelo com T010 (execuções independentes de pytest).
- T017 pode rodar em paralelo com T018.

---

## Parallel Example: User Story 1

```bash
# Mover os cinco testes de harness em paralelo (arquivos independentes):
Task: "git mv src/tests/test_block_git_push_hook.py src/tests/scripts/test_block_git_push_hook.py"
Task: "git mv src/tests/test_check_branch.py src/tests/scripts/test_check_branch.py"
Task: "git mv src/tests/test_check_commit_message.py src/tests/scripts/test_check_commit_message.py"
Task: "git mv src/tests/test_check_sensitive_paths.py src/tests/scripts/test_check_sensitive_paths.py"
Task: "git mv src/tests/test_report_scope_diff.py src/tests/scripts/test_report_scope_diff.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Completar Setup + Foundational.
2. Completar US1 (mover os testes).
3. Completar US2 (validar que tudo continua funcionando) — inseparável de US1 na prática, ambas P1.
4. **Parar e validar**: `poetry run pytest -q`.

### Incremental Delivery

1. Setup + Foundational → diretório de destino pronto.
2. US1 + US2 → testes movidos e funcionando (MVP).
3. US3 → convenção documentada.
4. Polish → validação completa.

## Notes

- Nenhum teste novo é criado nesta feature.
- Nenhum diretório especulativo é criado para módulos sem código de negócio (`src/player_modeling/*`).
- Commitar após a conclusão das user stories, conforme preferência do desenvolvedor — decisão humana, não automática.
