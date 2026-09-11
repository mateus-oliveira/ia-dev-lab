# ADR 0006 - Alembic para migrações do banco de dados

* **Status:** Aceito
* **Data:** 2026-09-11
* **Decisão:** Adoção do **Alembic** para gerenciar o schema do SQLite (`db.sqlite3`) por meio de migrações versionadas, substituindo a criação automática de tabelas no `lifespan` da API.

## Contexto

A [ADR 0004](0004-db-e-primeira-tabela-users.md) estabeleceu o `db.sqlite3` e a primeira tabela, `users`. Até esta decisão, o schema era criado por `init_db()` (`src/player_modeling/api/database.py`), um `CREATE TABLE IF NOT EXISTS` fixo no código, chamado automaticamente na inicialização da API ([ADR 0005](0005-fastapi-e-jwt-auth.md)).

Esse mecanismo não tem histórico de alterações de schema, não versiona mudanças e não permite reverter uma alteração. O projeto vai adicionar tabelas de domínio no futuro (eventos, sessões, perfis Bartle, conforme `docs/escopo.md`), tornando necessário um mecanismo de migração antes que o schema cresça de forma ad-hoc.

## Decisões

### 1. Alembic como ferramenta de migração
Alembic é a ferramenta padrão de migrações do ecossistema SQLAlchemy, com suporte a SQLite (incluindo o modo `batch`, necessário porque o SQLite não suporta `ALTER TABLE` completo). Alternativas consideradas:
- **Scripts SQL manuais versionados**: mais simples, mas exigiria reimplementar controle de revisão aplicada, ordenação e reversão.
- **`yoyo-migrations`**: mais leve, porém menos padrão de mercado; Alembic tem documentação e comunidade maiores, e já assume uma trajetória natural caso o projeto adote SQLAlchemy como camada de acesso a dados no futuro.

### 2. Migrações escritas manualmente, sem `--autogenerate`
A camada de acesso a dados atual usa `sqlite3` puro (sem ORM/`Table` objects do SQLAlchemy), então `--autogenerate` não está disponível. As migrações desta mudança são escritas manualmente com `op.create_table(...)` etc. Suficiente para o schema atual (uma tabela); se o projeto adotar SQLAlchemy Core/ORM no futuro, reavaliar o uso de autogeração.

### 3. `alembic.ini` na raiz, pacote de migrações em `src/alembic/`
`alembic.ini` fica na raiz do projeto (configuração, convenção do próprio Alembic, ao lado de `pyproject.toml`), apontando via `script_location` para `src/alembic/`. O pacote de migrações (`env.py`, `versions/`) fica dentro de `src/`, e não na raiz, porque acessa diretamente `player_modeling.api.database.get_db_path()` e reproduz o schema de `users` — é código de acesso a dados do backend, cabendo junto com os demais módulos de domínio (`simulator`, `worker`, `ml`, `api`), não uma ferramenta de harness como `scripts/`. `src/alembic/` não tem `__init__.py`, então não colide com o pacote `alembic` instalado (Python trata namespace packages sem `__init__.py` como prioridade mais baixa na resolução de import).

### 4. Schema deixa de ser criado automaticamente pela API
A chamada a `init_db()` foi removida do `lifespan` em `src/player_modeling/api/app.py`, e a própria função `init_db()` foi removida de `database.py`. A partir desta mudança, o schema é responsabilidade exclusiva das migrações, aplicadas manualmente com `poetry run alembic upgrade head` (ou `make migrate`) antes de subir a API. **Isso é uma mudança de comportamento (BREAKING)**: quem subir a API sem aplicar as migrações antes terá erros ao tentar usar rotas que dependem da tabela `users`.

### 5. Migração inicial e bancos já existentes
A migração inicial (`3977097f2a32_create_users_table.py`) reproduz o schema antes criado por `init_db()`, incluindo `sqlite_autoincrement=True` para preservar o comportamento de `AUTOINCREMENT` do SQLite (evita reaproveitamento de `id` de linhas deletadas). Para um `db.sqlite3` já existente (criado pelo mecanismo antigo), `poetry run alembic stamp head` marca o banco nessa revisão sem reexecutar o `CREATE TABLE`.

## Consequências

- **Positivas**:
  - Alterações de schema futuras (novas tabelas de domínio) passam a ser revisões incrementais, rastreáveis e reversíveis.
  - Comando único e documentado (`alembic upgrade head` / `make migrate`) para provisionar o banco em qualquer ambiente.
- **Negativas / Limitações**:
  - A API não cria mais o schema sozinha; esquecer de rodar as migrações antes de subir a API em um ambiente novo resulta em erros de tabela inexistente — mitigado por documentação no README/CLAUDE.md e pelo `Makefile`.
  - Migrações são escritas manualmente (sem autogeração), exigindo atenção para não divergirem do schema real conforme o projeto cresce.
