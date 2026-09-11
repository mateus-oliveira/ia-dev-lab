## Context

Hoje `src/player_modeling/api/database.py` expõe `init_db()`, chamada no `lifespan` de `src/player_modeling/api/app.py`, que executa um `CREATE TABLE IF NOT EXISTS users` fixo no código. Não há histórico de schema nem forma de aplicar alterações incrementais (ver proposal.md - Why). O banco é SQLite em arquivo (`db.sqlite3` na raiz, caminho configurável via `DATABASE_PATH`, ADR 0004), sem servidor externo.

## Goals / Non-Goals

**Goals:**
- Trocar a criação de schema ad-hoc por migrações versionadas com Alembic, aplicáveis via comando explícito (`poetry run alembic upgrade head`).
- Preservar bancos SQLite já existentes (com a tabela `users` criada pelo `init_db()` atual) sem perda de dados.
- Deixar o mecanismo pronto para novas tabelas de domínio serem adicionadas como novas revisões, sem exigir reestruturação.

**Non-Goals:**
- Não migrar de SQLite para outro SGBD.
- Não criar tabelas de domínio novas (eventos, sessões, perfis Bartle) nesta change.
- Não automatizar a aplicação de migrações no startup da API (aplicação continua manual/explícita, alinhado ao estágio de POC).

## Decisions

### 1. Alembic como ferramenta de migração
Alembic é a ferramenta padrão de migrações do ecossistema SQLAlchemy e tem suporte a SQLite, incluindo o modo `batch` necessário porque o SQLite não suporta `ALTER TABLE` completo (ex.: não é possível remover/alterar colunas diretamente — Alembic contorna isso recriando a tabela). Alternativas consideradas:
- **Scripts SQL manuais versionados** (sem framework): mais simples, mas exige reimplementar controle de revisão aplicada, ordenação e reversão — o que o Alembic já resolve.
- **`yoyo-migrations`**: mais leve, mas menos padrão de mercado; equipe já não tem familiaridade com nenhuma das duas, e Alembic tem documentação e comunidade maiores, além de já assumir uma trajetória natural caso o projeto evolua para usar SQLAlchemy como camada de acesso a dados no futuro.

Alembic normalmente pressupõe SQLAlchemy para autogeração de migrações a partir de models. Como a camada de acesso a dados atual usa `sqlite3` puro (sem ORM/`Table` objects do SQLAlchemy — ver `database.py`), as migrações desta change são **escritas manualmente** (`op.create_table(...)`), sem usar `--autogenerate`. Isso é suficiente para o schema atual (uma tabela) e evita introduzir SQLAlchemy como dependência nova só para gerar migrações.

### 2. Localização dos arquivos do Alembic
`alembic.ini` na raiz do projeto (convenção do Alembic, ao lado de `pyproject.toml`) e o pacote de migrações em `alembic/` (também na raiz), com `env.py` e `versions/`. Não foi colocado dentro de `src/player_modeling/` porque o Alembic não é um módulo de domínio do backend (`simulator`, `worker`, `ml`, `api`) — é uma ferramenta de harness/infraestrutura de banco, similar em espírito a `scripts/` (harness) descrito no `CLAUDE.md`, mas mantém a convenção padrão do próprio Alembic de ficar na raiz para simplificar os comandos (`alembic upgrade head` sem flags de config adicionais).

`env.py` lê o caminho do banco a partir da mesma função `get_db_path()` de `src/player_modeling/api/database.py` (via `sys.path` incluindo `src`, mesma técnica já usada em `src/tests/conftest.py`), para não duplicar a lógica de resolução de `DATABASE_PATH`.

### 3. Remoção de `init_db()` do lifespan, não da função em si
A função `init_db()` deixa de ser chamada em `app.py` (a API não cria mais schema implicitamente), mas a função pode ser removida de `database.py` já que sua responsabilidade passa a ser 100% coberta pela migração inicial do Alembic — mantê-la sem uso violaria a regra do `CLAUDE.md` de não manter código morto/half-finished. A task correspondente cobre a remoção e o ajuste dos testes que hoje chamam `init_db()` diretamente para popular o banco de teste (passam a rodar `alembic upgrade head` programaticamente ou usar `op.create_table` equivalente em fixture).

### 4. Migração inicial e bancos já existentes
A migração inicial cria a tabela `users` com o mesmo DDL hoje usado por `init_db()`. Para bancos SQLite que já existem (criados pelo mecanismo antigo), o comando `alembic stamp head` marca o banco como já estando nessa revisão sem reexecutar o `CREATE TABLE` (Alembic grava isso na tabela de controle `alembic_version`). Isso é uma operação manual documentada no README/ADR, não automatizada, pois é um passo único de transição.

## Risks / Trade-offs

- [Banco de dev existente sem `alembic_version`] → `alembic upgrade head` falharia com "table users already exists" → Mitigação: documentar no README/ADR o passo `alembic stamp head` para bancos pré-existentes, antes de rodar `upgrade`.
- [Escrever migrações manualmente sem autogeração] → risco de divergência entre migração e schema real ao longo do tempo → Mitigação: nesta change há só uma tabela simples; se o projeto adotar SQLAlchemy Core/ORM no futuro, reavaliar o uso de `--autogenerate` (fica registrado como ponto de atenção, não como decisão desta change).
- [Testes que hoje dependem de `init_db()`] → quebram se não forem ajustados → Mitigação: task explícita para atualizar `test_database.py` e qualquer fixture que use `init_db()` para aplicar a migração equivalente.

## Migration Plan

1. Adicionar dependência `alembic` ao `pyproject.toml` e `poetry.lock`.
2. Rodar `alembic init alembic` (ou estrutura equivalente criada manualmente) e configurar `env.py` para usar `get_db_path()`.
3. Criar a migração inicial com o DDL atual de `users`.
4. Remover a chamada a `init_db()` do `lifespan` em `app.py` e remover `init_db()` de `database.py`.
5. Ajustar testes que dependiam de `init_db()`.
6. Documentar no README/CLAUDE.md o novo comando de setup (`poetry run alembic upgrade head`) e, para quem já tem `db.sqlite3` local, `poetry run alembic stamp head`.
7. Registrar ADR 0006 com a decisão.

Rollback: como a mudança não altera dados, reverter é remover a pasta `alembic/`/`alembic.ini`, restaurar `init_db()` e sua chamada no `lifespan` (reverter o commit/PR desta change).
