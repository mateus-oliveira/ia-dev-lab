---
description: "Task list for feature 001-reorganizar-backend-src"
---

# Tasks: Reorganizar artefatos do backend sob src/

**Input**: Design documents from `/specs/001-reorganizar-backend-src/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [quickstart.md](./quickstart.md)

**Tests**: Não solicitados explicitamente na spec (mudança estrutural, sem lógica de negócio nova). A validação é feita via comandos existentes (`pytest`, `ruff`, `mypy`, `pre-commit`) e via `quickstart.md`, não via novos testes automatizados.

**Organization**: Tarefas agrupadas por user story da [spec.md](./spec.md) (US1 = P1, US2 = P2, US3 = P3), permitindo implementação e verificação independentes de cada uma.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependência de tarefa incompleta)
- **[Story]**: A qual user story da spec a tarefa pertence (US1, US2, US3)
- Caminhos de arquivo exatos em cada descrição

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Estabelecer uma baseline verificável antes de mover qualquer arquivo.

- [X] T001 Rodar `poetry run pytest`, `poetry run ruff check .` e `poetry run mypy .` a partir da raiz do repositório e confirmar que todos passam antes de qualquer mudança (baseline "verde" documentada, sem alteração de arquivos)
- [X] T002 [P] Calcular e registrar `sha256sum data/events.csv data/sessions_features.csv` (baseline para comparação pós-reorganização, conforme `quickstart.md` passo 2)

**Checkpoint**: Baseline confirmada — só prosseguir se T001 passou.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Tornar `src/player_modeling` um pacote Python rastreável no Git, pré-requisito de US1 e US2.

**⚠️ CRITICAL**: Nenhuma user story pode começar antes desta fase.

- [X] T003 Criar `src/player_modeling/__init__.py` com docstring de uma linha descrevendo o pacote (ex.: "Domínio de Player Modeling: API, ML, simulador e worker.")

**Checkpoint**: Pacote `player_modeling` existe e é importável — user stories podem começar.

---

## Phase 3: User Story 1 - Scripts do backend/pipeline agrupados sob src/ (Priority: P1) 🎯 MVP

**Goal**: Mover o script de operação da pipeline (`generate_raw_events.py`) para dentro de `src/`, mantendo os scripts de harness fora de `src/`, sem alterar comportamento.

**Independent Test**: Executar o script a partir do novo caminho sob `src/` e confirmar que `data/events.csv` e `data/sessions_features.csv` são gerados corretamente.

### Implementation for User Story 1

- [X] T004 [US1] Criar `src/player_modeling/scripts/__init__.py` com docstring descrevendo o propósito (scripts executáveis da pipeline/backend, distintos dos scripts de harness em `scripts/`)
- [X] T005 [US1] Mover `scripts/generate_raw_events.py` para `src/player_modeling/scripts/generate_raw_events.py` via `git mv`, sem alterar seu conteúdo/comportamento
- [X] T006 [US1] Atualizar todas as referências ao caminho antigo `scripts/generate_raw_events.py` em `CLAUDE.md` (seções "Executar o pipeline" e "Dados") para `src/player_modeling/scripts/generate_raw_events.py`
- [X] T007 [US1] Buscar e atualizar eventuais referências ao caminho antigo em `README.md` (`grep -rn "scripts/generate_raw_events.py" README.md`)
- [X] T008 [US1] Confirmar que `scripts/` contém apenas os scripts de harness (`block_git_push_hook.py`, `check_branch.py`, `check_commit_message.py`, `check_sensitive_paths.py`, `report_scope_diff.py`) via `find scripts -maxdepth 1 -type f -name "*.py" | sort`
- [X] T009 [US1] Executar `poetry run python src/player_modeling/scripts/generate_raw_events.py --players 200 --seed 42` a partir da raiz e confirmar que `data/events.csv` e `data/sessions_features.csv` são gerados sem erro (quickstart.md passo 2)

**Checkpoint**: User Story 1 completa e testável de forma independente — o script de pipeline funciona a partir do novo caminho.

---

## Phase 4: User Story 2 - Estrutura de domínio coerente e documentada (Priority: P2)

**Goal**: Tornar rastreável e documentada a separação por domínio (api, ml, simulator, worker) dentro de `src/player_modeling/`, sem introduzir código de negócio.

**Independent Test**: Revisar a árvore de `src/player_modeling/` e a documentação, confirmando que a separação por domínio está presente, rastreada no Git e descrita no `CLAUDE.md`.

### Implementation for User Story 2

- [X] T010 [P] [US2] Criar `src/player_modeling/api/__init__.py` com docstring: módulo do endpoint GET de consulta do perfil do jogador (ainda não implementado)
- [X] T011 [P] [US2] Criar `src/player_modeling/ml/__init__.py` com docstring: módulo de treinamento e inferência do modelo de perfil (Bartle) (ainda não implementado)
- [X] T012 [P] [US2] Criar `src/player_modeling/simulator/__init__.py` com docstring: módulo do simulador de eventos sintéticos (cronjob) (ainda não implementado)
- [X] T013 [P] [US2] Criar `src/player_modeling/worker/__init__.py` com docstring: módulo do worker/ETL que consome eventos da fila (ainda não implementado)
- [X] T014 [US2] Atualizar a seção "Organização" do `CLAUDE.md` para refletir a árvore final de `src/player_modeling/` (incluindo `scripts/` da US1) de forma consistente com o repositório (depende de T004-T013)

**Checkpoint**: User Stories 1 e 2 funcionam juntas — estrutura de domínio completa, rastreada e documentada.

---

## Phase 5: User Story 3 - Dados e testes agrupados sob src/, sem misturar com o código de domínio (Priority: P3)

**Goal**: Mover `data/` e `tests/` para dentro de `src/` (como irmãos de `player_modeling/`), já que `src/` passa a agrupar tudo o que é relacionado à implementação do backend — decisão confirmada com o desenvolvedor durante a implementação — sem alterar formato/finalidade dos dados nem a estrutura interna dos testes.

**Independent Test**: Confirmar que `src/data/` e `src/tests/` existem, que `data/`/`tests/` não existem mais na raiz, e que `poetry run pytest` continua passando.

### Implementation for User Story 3

- [X] T015 [US3] Mover `data/` para `src/data/` via `git mv` (irmão de `src/player_modeling/`, não aninhado nele), sem alterar o conteúdo dos CSVs
- [X] T015a [US3] Mover `tests/` para `src/tests/` via `git mv` (irmão de `src/player_modeling/`)
- [X] T015b [US3] Atualizar `pyproject.toml` (`[tool.pytest.ini_options] testpaths`) de `["tests"]` para `["src/tests"]`
- [X] T015c [US3] Corrigir `src/tests/conftest.py` (`SCRIPTS_DIR`) para subir 3 níveis (`parent.parent.parent`) até a raiz do repositório, já que o arquivo está um nível mais fundo
- [X] T015d [US3] Atualizar o default de `--outdir` em `src/player_modeling/scripts/generate_raw_events.py` de `"data"` para `"src/data"`, e `FLAGGED_PATHS` em `scripts/report_scope_diff.py` para `src/data/events.csv`/`src/data/sessions_features.csv` (e o teste correspondente em `src/tests/test_report_scope_diff.py`)
- [X] T015e [US3] Adicionar type hints às funções de `generate_raw_events.py` (`session_weights`, `generate_session`, `extract_features`, `main`, `run_sanity_check`, e anotar `PERSONA_PROFILES`), exigidos pelo override de mypy `player_modeling.*` após a movimentação do script para dentro do pacote
- [X] T016 [US3] Atualizar `CLAUDE.md`/`README.md` (árvore de diretórios, seção "Dados", seção "Testes") para `src/data/` e `src/tests/`, confirmando que a origem dos dados (`generate_raw_events.py`, novo caminho) continua documentada

**Checkpoint**: Todas as user stories completas — `data/` e `tests/` sob `src/`, dados íntegros (mesmo formato) e documentação consistente.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validação final de que nada quebrou fora do escopo das user stories.

- [X] T017 Rodar `poetry run pytest`, `poetry run ruff check .`, `poetry run ruff format --check .` e `poetry run mypy .` a partir da raiz e confirmar que todos passam após a reorganização (quickstart.md passo 3)
- [X] T018 Rodar `poetry run pre-commit run --all-files` e confirmar que passa sem falhas relacionadas à reorganização (quickstart.md passo 4)
- [X] T019 [P] Rodar `poetry run python scripts/report_scope_diff.py` (branch base `dev`) e revisar a lista de arquivos alterados, confirmando que só os caminhos esperados por esta feature foram tocados
- [X] T020 Revisar `git status`/`git diff` final e confirmar que nenhum arquivo de dados brutos, `.venv`, cache ou artefato gerado foi versionado acidentalmente

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências — pode começar imediatamente.
- **Foundational (Phase 2)**: Depende da conclusão do Setup — bloqueia todas as user stories.
- **User Story 1 (Phase 3)**: Depende apenas do Foundational.
- **User Story 2 (Phase 4)**: Depende do Foundational; T014 depende também de T004-T013 (US1) para descrever a árvore final completa.
- **User Story 3 (Phase 5)**: Depende de T002 (baseline) e, para T016, da conclusão de T006 (US1).
- **Polish (Phase 6)**: Depende de todas as user stories completas.

### User Story Dependencies

- **US1 (P1)**: Sem dependência de outras stories além do Foundational.
- **US2 (P2)**: Independente na criação dos `__init__.py` (T010-T013); apenas a tarefa de documentação final (T014) referencia o resultado de US1.
- **US3 (P3)**: Depende de artefatos de baseline (T002) e de documentação atualizada por US1 (T006) para sua tarefa de verificação (T016).

### Parallel Opportunities

- T002 pode rodar em paralelo com T001.
- T010, T011, T012, T013 podem rodar em paralelo entre si (arquivos diferentes).
- T019 pode rodar em paralelo com T020.

---

## Parallel Example: User Story 2

```bash
# Criar os quatro __init__.py de domínio em paralelo (arquivos independentes):
Task: "Criar src/player_modeling/api/__init__.py com docstring de propósito"
Task: "Criar src/player_modeling/ml/__init__.py com docstring de propósito"
Task: "Criar src/player_modeling/simulator/__init__.py com docstring de propósito"
Task: "Criar src/player_modeling/worker/__init__.py com docstring de propósito"
```

---

## Implementation Strategy

### MVP First (User Story 1 apenas)

1. Completar Phase 1: Setup (baseline).
2. Completar Phase 2: Foundational (`src/player_modeling/__init__.py`).
3. Completar Phase 3: User Story 1 (mover o script de pipeline).
4. **Parar e validar**: rodar `quickstart.md` passo 2 isoladamente.

### Incremental Delivery

1. Setup + Foundational → base pronta.
2. US1 → script de pipeline sob `src/`, testável isoladamente.
3. US2 → estrutura de domínio documentada e rastreada.
4. US3 → confirmação de que os dados não foram tocados.
5. Polish → validação completa (testes, lint, mypy, pre-commit, diff de escopo).

## Notes

- Esta feature não introduz testes novos: a verificação é feita pela suíte existente (`poetry run pytest`) e pelos passos manuais de `quickstart.md`.
- Commitar após cada user story concluída (ou ao final, conforme preferência do desenvolvedor) — a decisão de quando commitar é humana, não automática.
- Evitar: mover mais arquivos do que o necessário, alterar o conteúdo do script durante a movimentação, ou deixar referências ao caminho antigo em qualquer documento.
