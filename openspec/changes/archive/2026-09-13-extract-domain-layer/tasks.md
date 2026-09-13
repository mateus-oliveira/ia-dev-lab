## 1. Camada de domínio

- [x] 1.1 Criar `src/player_modeling/domain/personas.py` com o Enum `BartlePersona` (na ordem atual de `PERSONAS`) e a lista `PERSONAS` derivada dele.
- [x] 1.2 Criar `src/player_modeling/domain/events.py` com `EVENT_TYPES`, movido de `simulator/events.py`.
- [x] 1.3 Criar `src/player_modeling/domain/features.py` com `FEATURE_COLUMNS` e `LABEL_COLUMN`, movidos de `ml/persona_model.py`.
- [x] 1.4 Criar `src/player_modeling/domain/__init__.py` documentando o critério de entrada da camada.

## 2. Camada de persistência

- [x] 2.1 Criar `src/player_modeling/persistence/database.py` com `DEFAULT_DATABASE_PATH`, `get_db_path` e `get_connection`, movidos de `api/database.py`.
- [x] 2.2 Reduzir `api/database.py` à dependency `get_db` do FastAPI, importando `get_connection` da persistência.

## 3. Apontar os consumidores

- [x] 3.1 `api/schemas.py` importa `BartlePersona` do domínio e a re-exporta via `__all__`.
- [x] 3.2 `ml/persona_model.py` importa `BartlePersona`, `FEATURE_COLUMNS` e `LABEL_COLUMN` do domínio.
- [x] 3.3 `simulator/events.py` importa `EVENT_TYPES` e `PERSONAS` do domínio.
- [x] 3.4 `worker/features.py` importa `EVENT_TYPES` do domínio (deixando de depender de `simulator/`).
- [x] 3.5 `worker/subscriber.py` e `alembic/env.py` importam de `persistence/` (deixando de depender de `api/`).
- [x] 3.6 Atualizar os imports dos 8 arquivos de teste que apontam para `api.database`.

## 4. Garantia da regra

- [x] 4.1 Criar `src/tests/player_modeling/domain/test_domain_layer.py` verificando, por análise do código-fonte, que nenhum módulo de `domain/` importa outro módulo de `player_modeling`, e que o conjunto de valores de `BartlePersona` coincide com `PERSONAS`.
- [x] 4.2 Verificar com `grep` que não restou nenhuma das quatro dependências invertidas listadas no `proposal.md`.
- [x] 4.3 Rodar `poetry run pytest` e confirmar 208+ testes verdes sem nenhuma asserção alterada.

## 5. Qualidade e documentação

- [x] 5.1 Rodar `poetry run ruff check .`, `poetry run ruff format .` e `poetry run mypy .`.
- [x] 5.2 Atualizar a árvore de diretórios e a seção de organização de `README.md` e `CLAUDE.md`.
- [x] 5.3 Criar a ADR registrando a decisão arquitetural (camada de domínio, e a rejeição explícita de extrair serviço).
- [x] 5.4 Executar `poetry run python scripts/report_scope_diff.py dev` e confirmar que não há alterações em `src/data/`.
