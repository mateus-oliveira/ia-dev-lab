# Phase 1 Data Model: Reorganizar artefatos do backend sob src/

Esta feature é uma reorganização de arquivos, não um modelo de dados de aplicação. As "entidades" abaixo são artefatos do sistema de arquivos/repositório, mapeadas a partir da seção "Key Entities" da spec.

## Módulo de domínio (`src/player_modeling/*`)

- **Representação**: diretório Python com `__init__.py`.
- **Atributos**: nome do domínio (`api`, `ml`, `simulator`, `worker`), docstring de propósito no `__init__.py`.
- **Regras**: não deve conter lógica de negócio nesta feature; deve existir e ser rastreável no Git.
- **Relacionamentos**: agrupados sob o pacote pai `src/player_modeling/`.

## Script de pipeline (`src/player_modeling/scripts/generate_raw_events.py`)

- **Representação**: arquivo `.py` executável via `poetry run python <caminho>`.
- **Atributos**: argumentos de CLI (`--players`, `--seed`, `--outdir` com novo default `src/data`, `--sanity-check`), saída em `src/data/events.csv` e `src/data/sessions_features.csv`.
- **Regras**: comportamento observável (argumentos e formato de saída) preservado; funções ganharam type hints (exigido pelo override de mypy `player_modeling.*` após a movimentação), sem alterar a lógica.
- **Relacionamentos**: pertence ao pacote `player_modeling` (mesmo domínio do modelo de ML que consome seu output); é referenciado por `CLAUDE.md`/`README.md`.

## Script de harness (`scripts/*.py`, exceto `generate_raw_events.py`)

- **Representação**: arquivos `.py` em `scripts/` na raiz.
- **Atributos**: `block_git_push_hook.py`, `check_branch.py`, `check_commit_message.py`, `check_sensitive_paths.py`, `report_scope_diff.py`.
- **Regras**: permanecem fora de `src/`; `report_scope_diff.py` teve seus `FLAGGED_PATHS` atualizados para `src/data/events.csv` e `src/data/sessions_features.csv`.
- **Relacionamentos**: referenciados por `.pre-commit-config.yaml`, CI e `src/tests/`.

## Dataset sintético (`src/data/events.csv`, `src/data/sessions_features.csv`)

- **Representação**: arquivos CSV, agora sob `src/data/` (irmão de `src/player_modeling/`, não aninhado nele).
- **Atributos**: gerados por `src/player_modeling/scripts/generate_raw_events.py`; `sessions_features.csv` inclui `true_persona`.
- **Regras**: formato e finalidade inalterados; o conteúdo pode ser regenerado (mesma seed/parâmetros) como parte da validação, o que é esperado (ver `quickstart.md`).
- **Relacionamentos**: produzidos pelo script de pipeline; consumidos futuramente pelo módulo `ml`.

## Suíte de testes (`src/tests/`)

- **Representação**: diretório movido de `tests/` (raiz) para `src/tests/`, irmão de `src/player_modeling/`.
- **Atributos**: `conftest.py` (ajustado para resolver `SCRIPTS_DIR` subindo 3 níveis até a raiz do repo) e os arquivos `test_*.py` existentes, sem reorganização interna.
- **Regras**: `pyproject.toml` (`testpaths`) aponta para `src/tests`; a suíte deve continuar passando via `poetry run pytest`.
- **Relacionamentos**: o espelhamento interno por módulo (ex.: `src/tests/scripts/test_check_branch.py`) é escopo do item 5 do escopo (feature `002-*`), não desta feature.
