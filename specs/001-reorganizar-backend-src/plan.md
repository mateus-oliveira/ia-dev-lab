# Implementation Plan: Reorganizar artefatos do backend sob src/

**Branch**: `refactor/with-gh-spec-kit` | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-reorganizar-backend-src/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Reorganizar os artefatos do backend/pipeline para ficarem agrupados sob `src/`, sem alterar comportamento nem introduzir código de negócio novo: (1) mover `scripts/generate_raw_events.py` — o único script de operação da pipeline hoje fora de `src/` — para `src/player_modeling/scripts/generate_raw_events.py`; (2) tornar rastreáveis no Git os diretórios de domínio hoje vazios (`src/player_modeling/{api,ml,simulator,worker}`) via `__init__.py` com docstring de propósito; (3) manter `scripts/` apenas com ferramentas de harness; (4) manter `data/` inalterado fora de `src/`; (5) atualizar todas as referências (`CLAUDE.md`, `README.md`, `pyproject.toml` se necessário) para o novo caminho do script.

## Technical Context

**Language/Version**: Python 3.13 (já em uso no projeto, ver `pyproject.toml`)

**Primary Dependencies**: Nenhuma nova. Usa apenas a stdlib (`argparse`, `csv`, `os`, `random`, `uuid`, `datetime`) já usada por `generate_raw_events.py`, e o toolchain de dev existente (Poetry, ruff, mypy, pytest).

**Storage**: Arquivos CSV em `data/` (`events.csv`, `sessions_features.csv`) — inalterado por esta feature.

**Testing**: `pytest` via `poetry run pytest`, conforme `pyproject.toml` (`testpaths = ["tests"]`).

**Target Platform**: Ambiente de desenvolvimento local (POC acadêmica); execução via CLI (`poetry run python ...`).

**Project Type**: Projeto único Python (não é web app nem mobile) — layout `src/` + `tests/` na raiz.

**Performance Goals**: N/A — mudança puramente estrutural, sem impacto de performance esperado.

**Constraints**: Preservar 100% o comportamento observável dos comandos existentes (mesmos argumentos, mesma saída em `data/`); não introduzir código de negócio; não quebrar `poetry run pytest`, `ruff`, `mypy` nem os hooks de pré-commit.

**Scale/Scope**: Repositório pequeno (POC de disciplina); esta feature toca 1 script executável, 4 diretórios de domínio vazios, e a documentação (`CLAUDE.md`/`README.md`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

O arquivo `.specify/memory/constitution.md` ainda está no estado de template (não foi ratificado com princípios do projeto — decisão consciente: as regras de desenvolvimento deste projeto já vivem em `CLAUDE.md` e nos ADRs em `docs/adr/`, que cumprem esse papel). Portanto, o gate desta feature é a conformidade com `CLAUDE.md` e com a ADR 0002 (GitFlow), não com `constitution.md`.

Checagens relevantes de `CLAUDE.md` aplicadas a este plano:

- ✅ Não implementa funcionalidades de negócio antecipadas (seção "Não fazer"): esta feature é estrutural.
- ✅ Não modifica dados brutos (`data/events.csv`, `data/sessions_features.csv` permanecem intocados).
- ✅ Não adiciona dependências novas.
- ✅ Preserva testes existentes e comandos documentados (serão atualizados, não quebrados).
- ✅ Mudança será revisada por humano antes de commit/push (nenhum commit automático nesta sessão).

Nenhuma violação identificada. Nada a registrar em "Complexity Tracking".

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/                              # tudo o que é relacionado à implementação do backend
├── player_modeling/
│   ├── __init__.py              # NOVO — torna o pacote rastreável no Git
│   ├── api/
│   │   └── __init__.py          # NOVO — placeholder documentado, sem lógica
│   ├── ml/
│   │   └── __init__.py          # NOVO — placeholder documentado, sem lógica
│   ├── simulator/
│   │   └── __init__.py          # NOVO — placeholder documentado, sem lógica
│   ├── worker/
│   │   └── __init__.py          # NOVO — placeholder documentado, sem lógica
│   └── scripts/
│       ├── __init__.py          # NOVO
│       └── generate_raw_events.py   # MOVIDO de scripts/generate_raw_events.py
├── data/                         # MOVIDO de data/ (raiz) — irmão de player_modeling/, não aninhado nele
│   ├── events.csv
│   └── sessions_features.csv
└── tests/                        # MOVIDO de tests/ (raiz) — irmão de player_modeling/
    ├── conftest.py               # ajustado: SCRIPTS_DIR agora sobe 3 níveis até a raiz
    ├── test_block_git_push_hook.py
    ├── test_check_branch.py
    ├── test_check_commit_message.py
    ├── test_check_sensitive_paths.py
    └── test_report_scope_diff.py

scripts/                          # inalterado, exceto pela remoção do arquivo movido — só harness
├── block_git_push_hook.py
├── check_branch.py
├── check_commit_message.py
├── check_sensitive_paths.py
└── report_scope_diff.py          # FLAGGED_PATHS atualizado para src/data/*.csv
```

**Structure Decision**: Opção "projeto único" (não há frontend/mobile). `src/` passa a ser o container de tudo relacionado ao backend — confirmado com o desenvolvedor durante a implementação, revisando a decisão inicial deste plano (que mantinha `data/` e `tests/` na raiz). Três movimentos de diretório/arquivo:

1. `scripts/generate_raw_events.py` → `src/player_modeling/scripts/generate_raw_events.py` — dentro do domínio `player_modeling`, pois gera o dataset usado para pré-treinar o modelo desse domínio (convenção de organização por domínio do `CLAUDE.md`).
2. `data/` → `src/data/` — irmão de `player_modeling/`, não aninhado nele (dados não são código de domínio).
3. `tests/` → `src/tests/` — irmão de `player_modeling/`; apenas a localização muda nesta feature, o espelhamento interno por módulo é escopo do item 5 (feature `002-*`).

`scripts/` (harness) permanece na raiz — fica fora do container `src/` por não ser parte do backend, apenas ferramentas de validação do processo de desenvolvimento.

Os quatro subpacotes de domínio (`api`, `ml`, `simulator`, `worker`) ganham `__init__.py` apenas para existirem no Git e documentar seu propósito — nenhuma lógica de negócio é adicionada.

Consequência técnica do movimento 1: como `src/player_modeling/scripts/generate_raw_events.py` passa a fazer parte do pacote `player_modeling`, o override de mypy `disallow_untyped_defs` (aplicado a `player_modeling.*`) passou a exigir type hints em suas funções — adicionados sem alterar comportamento.

## Complexity Tracking

Não aplicável — o Constitution Check não identificou violações a justificar.
