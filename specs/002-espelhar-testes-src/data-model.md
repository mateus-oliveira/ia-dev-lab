# Phase 1 Data Model: Espelhar src/tests/ pela organização dos módulos verificados

Reorganização de arquivos de teste, não modelo de dados de aplicação. Entidades mapeadas a partir da seção "Key Entities" da spec.

## Teste de harness (`src/tests/scripts/test_*.py`)

- **Representação**: arquivo `.py` com prefixo `test_`, movido de `src/tests/` para `src/tests/scripts/`.
- **Atributos**: nome idêntico ao script que verifica (`test_check_branch.py` ↔ `scripts/check_branch.py`).
- **Regras**: conteúdo lógico (asserts, casos de teste) inalterado; apenas a localização muda.
- **Relacionamentos**: verifica um script específico em `scripts/` (raiz); depende de `conftest.py` para import.

## Configuração compartilhada (`src/tests/conftest.py`)

- **Representação**: arquivo de configuração do pytest na raiz da suíte.
- **Atributos**: define `SCRIPTS_DIR` e insere em `sys.path`.
- **Regras**: permanece em `src/tests/`, não duplicado; continua sendo herdado por `src/tests/scripts/` automaticamente.
- **Relacionamentos**: usado implicitamente por todos os testes sob `src/tests/`.

## Convenção de espelhamento (documentação)

- **Representação**: texto na seção "Testes" do `CLAUDE.md`.
- **Atributos**: regra genérica ("cada teste fica no caminho de `src/tests/` correspondente ao módulo verificado") + exemplo concreto do estado atual.
- **Regras**: não gera arquivos ou diretórios — é só documentação, aplicável a testes futuros.
- **Relacionamentos**: referencia `scripts/` (atual) e `src/player_modeling/*` (futuro).
