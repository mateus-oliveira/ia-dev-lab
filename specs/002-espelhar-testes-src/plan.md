# Implementation Plan: Espelhar src/tests/ pela organização dos módulos verificados

**Branch**: `refactor/tests-organization` | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-espelhar-testes-src/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Mover os cinco testes de harness (`test_block_git_push_hook.py`, `test_check_branch.py`, `test_check_commit_message.py`, `test_check_sensitive_paths.py`, `test_report_scope_diff.py`) de `src/tests/` para `src/tests/scripts/`, espelhando o diretório `scripts/` (raiz) que eles verificam, mantendo `src/tests/conftest.py` na raiz da suíte (o pytest propaga `conftest.py` para subdiretórios automaticamente). Nenhum diretório de teste é criado para os módulos de `src/player_modeling/*` (ainda sem código de negócio). Atualizar `CLAUDE.md` para documentar a convenção de espelhamento.

## Technical Context

**Language/Version**: Python 3.13 (já em uso no projeto)

**Primary Dependencies**: Nenhuma nova. `pytest` (já em uso); nenhuma mudança em `import` dentro dos próprios testes (continuam importando os scripts de harness pelo nome do módulo, ex.: `from check_branch import ...`), já que `conftest.py` insere `scripts/` no `sys.path`.

**Storage**: N/A — mudança estrutural de arquivos, sem dados.

**Testing**: `pytest` via `poetry run pytest`, `testpaths = ["src/tests"]` (já configurado na feature 001, cobre subdiretórios recursivamente sem mudança).

**Target Platform**: Ambiente de desenvolvimento local e CI (GitHub Actions), ambos rodando `poetry run pytest` a partir da raiz do repositório.

**Project Type**: Projeto único Python — mudança restrita a `src/tests/`.

**Performance Goals**: N/A — mudança estrutural, sem impacto de performance.

**Constraints**: Preservar 100% o comportamento e a cobertura dos testes existentes; não criar estrutura de teste especulativa para módulos sem código; não duplicar `conftest.py`.

**Scale/Scope**: 5 arquivos de teste movidos + 1 diretório novo (`src/tests/scripts/`) + atualização de documentação.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Como na feature 001, `.specify/memory/constitution.md` permanece no estado de template; o gate real desta feature é a conformidade com `CLAUDE.md` e ADR 0002/0003.

Checagens aplicadas:

- ✅ Não implementa funcionalidades de negócio antecipadas — mudança estrutural de testes.
- ✅ Não cria diretórios de teste especulativos para módulos sem código (`src/player_modeling/{api,ml,simulator,worker,scripts}`), respeitando a seção "Não fazer" do `CLAUDE.md`.
- ✅ Preserva testes existentes: nenhum caso de teste é removido, alterado ou perde cobertura.
- ✅ Não adiciona dependências novas.
- ✅ Mudança será revisada por humano antes de commit/push.

Nenhuma violação identificada.

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
src/
├── player_modeling/               # inalterado nesta feature (sem testes ainda)
│   ├── api/
│   ├── ml/
│   ├── simulator/
│   ├── worker/
│   └── scripts/
├── data/                          # inalterado
└── tests/
    ├── conftest.py                # permanece na raiz da suíte (não duplicado)
    └── scripts/                   # NOVO — espelha scripts/ (raiz)
        ├── test_block_git_push_hook.py     # MOVIDO de src/tests/
        ├── test_check_branch.py            # MOVIDO de src/tests/
        ├── test_check_commit_message.py    # MOVIDO de src/tests/
        ├── test_check_sensitive_paths.py   # MOVIDO de src/tests/
        └── test_report_scope_diff.py       # MOVIDO de src/tests/

scripts/                           # inalterado — módulo verificado pelos testes acima
├── block_git_push_hook.py
├── check_branch.py
├── check_commit_message.py
├── check_sensitive_paths.py
└── report_scope_diff.py
```

**Structure Decision**: Projeto único (mesma decisão da feature 001). Único diretório novo: `src/tests/scripts/`, espelhando `scripts/` (raiz), que é o único módulo com testes hoje. `src/tests/conftest.py` permanece na raiz da suíte porque o pytest aplica automaticamente um `conftest.py` a todos os subdiretórios abaixo dele — duplicá-lo violaria FR-002 sem necessidade. Nenhum diretório é criado sob `src/tests/` para `player_modeling/*` nesta feature (FR-004): a convenção fica documentada em `CLAUDE.md` para uso quando esses módulos ganharem testes reais.

## Complexity Tracking

Não aplicável — o Constitution Check não identificou violações a justificar.
