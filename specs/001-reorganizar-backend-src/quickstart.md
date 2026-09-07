# Quickstart: Validar a reorganização do backend sob src/

Guia para confirmar, manualmente, que a reorganização (feature `001-reorganizar-backend-src`) preserva o comportamento existente. Ver `data-model.md` para os artefatos envolvidos e `spec.md` para os critérios de aceitação (FR-001..FR-010, SC-001..SC-005).

## Pré-requisitos

- Dependências instaladas: `poetry install`
- Rodar todos os comandos a partir da raiz do repositório.

## 1. Estrutura de diretórios

```bash
find src -maxdepth 2 | sort
find scripts -maxdepth 1 -type f -name "*.py" | sort
test -d data && echo "ERRO: data/ ainda existe na raiz" || echo "OK: data/ não existe na raiz"
test -d tests && echo "ERRO: tests/ ainda existe na raiz" || echo "OK: tests/ não existe na raiz"
```

**Esperado**: `src/player_modeling/scripts/generate_raw_events.py` existe; `src/player_modeling/{__init__.py,api/__init__.py,ml/__init__.py,simulator/__init__.py,worker/__init__.py}` existem; `src/data/` e `src/tests/` existem como irmãos de `src/player_modeling/`; `data/` e `tests/` não existem mais na raiz; `scripts/` contém apenas os 5 scripts de harness (sem `generate_raw_events.py`).

## 2. Geração do dataset a partir do novo caminho

```bash
# hash antes de qualquer regeneração, para comparação
sha256sum src/data/events.csv src/data/sessions_features.csv

poetry run python src/player_modeling/scripts/generate_raw_events.py --players 200 --seed 42

sha256sum src/data/events.csv src/data/sessions_features.csv
```

**Esperado**: comando executa sem erro e escreve em `src/data/` (novo default de `--outdir`); com a mesma seed e o mesmo `--players`, o conteúdo gerado tem o mesmo formato (mesmas colunas, mesmo número de linhas) do gerado antes da reorganização — o hash pode mudar entre execuções já feitas durante a implementação, o que é esperado.

## 3. Suíte de testes, lint e type-check inalterados

```bash
poetry run pytest
poetry run ruff check .
poetry run ruff format --check .
poetry run mypy .
```

**Esperado**: todos passam, sem referenciar o caminho antigo `scripts/generate_raw_events.py`.

## 4. Hooks de pré-commit

```bash
poetry run pre-commit run --all-files
```

**Esperado**: passa sem falhas relacionadas à reorganização (os scripts de harness continuam nos mesmos caminhos).

## 5. Documentação consistente

```bash
grep -rn "scripts/generate_raw_events.py" CLAUDE.md README.md docs/ 2>/dev/null
```

**Esperado**: nenhuma ocorrência do caminho antigo — todas as referências devem apontar para `src/player_modeling/scripts/generate_raw_events.py`, `src/data/` e `src/tests/`.
