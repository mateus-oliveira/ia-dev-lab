# Quickstart: Validar o espelhamento de src/tests/

Guia para confirmar manualmente que a reorganização (feature `002-espelhar-testes-src`) preserva o comportamento e a cobertura dos testes existentes. Ver `data-model.md` para os artefatos e `spec.md` para os critérios de aceitação (FR-001..FR-008, SC-001..SC-005).

## Pré-requisitos

- Dependências instaladas: `poetry install`
- Rodar todos os comandos a partir da raiz do repositório.

## 1. Estrutura de diretórios

```bash
find src/tests -type f -name "*.py" | sort
```

**Esperado**: `src/tests/conftest.py` na raiz; os 5 testes de harness em `src/tests/scripts/`; nenhum arquivo solto de teste em `src/tests/` além de `conftest.py`; nenhum diretório novo sob `src/tests/player_modeling/`.

## 2. Suíte completa

```bash
poetry run pytest -q
```

**Esperado**: mesmo número de testes coletados e aprovados de antes da reorganização (46), sem erro de import.

## 3. Teste individual pelo novo caminho

```bash
poetry run pytest src/tests/scripts/test_check_branch.py -v
poetry run pytest src/tests/scripts/test_report_scope_diff.py -v
```

**Esperado**: cada arquivo executa isoladamente sem erro de import do script de harness correspondente.

## 4. Lint, formatação e tipos inalterados

```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run mypy .
```

**Esperado**: todos passam.

## 5. Hooks de pré-commit

```bash
poetry run pre-commit run --all-files
```

**Esperado**: passa sem falhas relacionadas à reorganização.

## 6. Documentação consistente

```bash
grep -n "src/tests" CLAUDE.md README.md
```

**Esperado**: a seção "Testes" do `CLAUDE.md` descreve a convenção de espelhamento e referencia `src/tests/scripts/` como exemplo atual.
