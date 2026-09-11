## Why

Hoje o schema do SQLite (`db.sqlite3`) é criado por `init_db()` em `src/player_modeling/api/database.py`, com um único `CREATE TABLE IF NOT EXISTS users` embutido no código Python (ADR 0004). Esse mecanismo não versiona alterações de schema, não tem histórico de mudanças e não tem como aplicar migrações incrementais ou reverter uma alteração. O projeto vai adicionar/alterar tabelas em breve (eventos, sessões, perfis Bartle, conforme o pipeline descrito em `docs/escopo.md` e no `CLAUDE.md`), então é necessário adotar uma ferramenta de migração antes que o schema cresça de forma ad-hoc.

## What Changes

- Adicionar **Alembic** como dependência de desenvolvimento/runtime do projeto, configurado para o SQLite usado hoje (`db.sqlite3`, caminho configurável via `DATABASE_PATH`).
- Criar a estrutura padrão do Alembic (`alembic.ini`, diretório `alembic/` com `env.py` e `versions/`) dentro da árvore do projeto, respeitando a convenção de organização por domínio do `CLAUDE.md`.
- Criar a migração inicial (`0001_create_users_table` ou equivalente) que reproduz exatamente o schema hoje criado por `init_db()` (tabela `users` da ADR 0004), para que bancos existentes fiquem "carimbados" nessa revisão sem precisar recriar dados.
- **BREAKING**: remover a criação de schema via `init_db()` chamada no `lifespan` da aplicação (`src/player_modeling/api/app.py`); a partir desta mudança, o schema passa a ser aplicado exclusivamente via `alembic upgrade head`, executado manualmente ou em um passo de setup/deploy — a API não cria mais tabelas na inicialização.
- Atualizar `README.md` e `CLAUDE.md` com o novo comando de setup do banco (`poetry run alembic upgrade head`) substituindo a menção implícita ao `init_db()` automático.
- Registrar a decisão em uma nova ADR (`docs/adr/0006-...md`), já que se trata de uma decisão arquitetural relevante que complementa a ADR 0004.

Fora de escopo desta change (ver seção "Não fazer" do `CLAUDE.md`):
- Não serão criadas novas tabelas de negócio (eventos, sessões, perfis Bartle) — apenas a infraestrutura de migração e a migração equivalente ao schema atual de `users`.
- Não haverá alteração de frontend, autenticação/autorização (além do que já existe), endpoints adicionais, integrações externas (PlayFab, Databricks, Redis) ou infraestrutura de produção/deploy.
- Não haverá migração de dados de `db.sqlite3` para outro SGBD (ex.: Postgres) — a mudança é só a forma de versionar o schema SQLite já em uso.

## Capabilities

### New Capabilities
- `database-migrations`: gerenciamento versionado do schema do banco de dados SQLite via Alembic (estrutura de migrações, comando de aplicação, migração inicial equivalente ao schema atual).

### Modified Capabilities
(nenhuma — não há capability de API/autenticação especificada em `openspec/specs/` hoje; a mudança em `app.py`/`database.py` é detalhe de implementação da nova capability acima, não uma alteração de requisito de uma spec existente.)

## Impact

- **Código afetado**: `src/player_modeling/api/database.py` (remoção de `init_db()` como criador de schema), `src/player_modeling/api/app.py` (remoção da chamada a `init_db()` no `lifespan`).
- **Novos arquivos**: `alembic.ini`, `alembic/env.py`, `alembic/versions/<revisão inicial>.py`.
- **Dependências**: nova dependência `alembic` em `pyproject.toml` (grupo principal, pois pode ser necessária em ambientes de deploy/CI para aplicar migrações, não só em dev).
- **Testes**: testes de `src/tests/player_modeling/api/test_database.py` que hoje dependem de `init_db()` criar a tabela `users` precisam passar a rodar as migrações Alembic (ou uma função equivalente de setup de teste) antes de exercitar o banco.
- **Documentação**: `README.md`, `CLAUDE.md` e nova ADR em `docs/adr/`.
