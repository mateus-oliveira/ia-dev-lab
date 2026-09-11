## 1. Dependência e estrutura do Alembic

- [x] 1.1 Adicionar `alembic` como dependência em `pyproject.toml` (grupo principal) e atualizar `poetry.lock` via `poetry lock`; verificar com `poetry install` sem erros
- [x] 1.2 Gerar a estrutura `alembic.ini` (raiz do projeto) e `src/alembic/env.py` + `src/alembic/versions/`; verificar que `poetry run alembic current` executa sem erro de configuração (mesmo sem revisões ainda)
- [x] 1.3 Configurar `src/alembic/env.py` para resolver o caminho do banco via `get_db_path()` de `player_modeling.api.database` (adicionando `src` ao `sys.path`, como em `src/tests/conftest.py`), respeitando `DATABASE_PATH`; verificar rodando `poetry run alembic current` com `DATABASE_PATH` customizado e confirmando (via log/print temporário ou teste) que aponta para o caminho esperado

## 2. Migração inicial

- [x] 2.1 Criar a revisão inicial (`op.create_table` manual, sem autogenerate) reproduzindo exatamente o DDL de `users` hoje criado por `init_db()` (id, name, username único, password); verificar aplicando `poetry run alembic upgrade head` em um banco novo (arquivo temporário) e inspecionando o schema resultante (`PRAGMA table_info(users)`)
- [x] 2.2 Verificar que `poetry run alembic downgrade -1` a partir da revisão inicial remove a tabela `users` corretamente, confirmando a reversão

## 3. Remoção da criação de schema ad-hoc

- [x] 3.1 Remover a chamada a `init_db()` do `lifespan` em `src/player_modeling/api/app.py`; verificar que a API sobe normalmente com `poetry run uvicorn player_modeling.api.app:app` sem criar `db.sqlite3` automaticamente
- [x] 3.2 Remover a função `init_db()` de `src/player_modeling/api/database.py` (schema passa a ser responsabilidade exclusiva das migrações); verificar com `mypy`/`ruff` que não há referências órfãs

## 4. Ajuste dos testes existentes

- [x] 4.1 Atualizar `src/tests/player_modeling/api/test_database.py` e qualquer fixture que dependa de `init_db()` para aplicar o schema via Alembic (ex.: chamando `alembic.command.upgrade` programaticamente contra um banco temporário) em vez da função removida; verificar com `poetry run pytest src/tests/player_modeling/api/test_database.py`
- [x] 4.2 Rodar a suíte completa e confirmar que nenhum outro teste (`test_register.py`, `test_login.py`, `test_protected_routes.py`, etc.) dependia implicitamente de `init_db()`; verificar com `poetry run pytest`

## 5. Documentação

- [x] 5.1 Atualizar `README.md` e `CLAUDE.md` com o novo passo de setup do banco (`poetry run alembic upgrade head`) e a orientação para bancos `db.sqlite3` já existentes (`poetry run alembic stamp head`); verificar revisão manual do texto
- [x] 5.2 Criar `docs/adr/0006-alembic-migracoes-banco.md` documentando a decisão (Alembic, migrações manuais sem autogenerate, localização dos arquivos na raiz), referenciando a ADR 0004; verificar que segue o formato das ADRs existentes (status, data, decisão, contexto, decisões, consequências)

## 6. Makefile

- [x] 6.1 Criar `Makefile` na raiz com alvos `migrate` (alembic upgrade head), `migrate-down` (alembic downgrade -1), `migrate-stamp` (alembic stamp head), `test` (pytest) e `api` (uvicorn com PYTHONPATH=src); verificar executando cada alvo manualmente e confirmando o comportamento esperado
- [x] 6.2 Documentar os alvos do Makefile no README.md, indicando que alvos de worker/simulador serão adicionados quando esses módulos existirem; verificar revisão manual do texto

## 7. Validação final

- [x] 7.1 Rodar `poetry run ruff check .`, `poetry run ruff format --check .` e `poetry run mypy .`; verificar que passam sem erros
- [x] 7.2 Rodar `poetry run pytest` completo; verificar 100% dos testes passando
- [x] 7.3 Rodar `poetry run python scripts/report_scope_diff.py` e revisar o diff de escopo antes de considerar a change concluída
