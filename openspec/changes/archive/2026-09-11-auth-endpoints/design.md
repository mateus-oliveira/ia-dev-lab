## Context

Ver `proposal.md` para motivação e escopo da inclusão da camada de autenticação.
A arquitetura do projeto organiza o código em `src/player_modeling/api/` com tipagem estrita via MyPy (`disallow_untyped_defs = true`) e testes em `src/tests/player_modeling/api/` (alinhado a `pyproject.toml` e ADR 0003).

A persistência de usuários adota SQLite (`db.sqlite3` na raiz) conforme definido na [ADR 0004](file:///c:/Users/ander/Documents/ia-dev-lab/docs/adr/0004-db-e-primeira-tabela-users.md), garantindo simplicidade sem infraestrutura de banco de dados externa na POC. O fluxo de desenvolvimento segue estritamente o GitFlow da [ADR 0002](file:///c:/Users/ander/Documents/ia-dev-lab/docs/adr/0002-git-flow.md).

## Goals / Non-Goals

**Goals:**
- Implementar endpoints RESTful assíncronos para registro (`POST /auth/register`) e autenticação (`POST /auth/login`) na API FastAPI.
- Persistir usuários na tabela `users` do banco `db.sqlite3` com senhas hasheadas via bcrypt.
- Implementar dependência FastAPI (`get_current_user`) para validação de Bearer Token JWT e injeção de contexto do usuário nas rotas protegidas.
- Garantir tipagem 100% estrita em conformidade com o MyPy do projeto.
- Espelhar testes unitários e de integração em `src/tests/player_modeling/api/`.

**Non-Goals:**
- Implementar interface gráfica (frontend).
- Implementar fluxos complexos como recuperação de senha por e-mail, MFA ou refresh tokens rotativos.
- Alterar dados em `src/data/` ou acoplar autenticação a plataformas externas (ex.: PlayFab).
- Adicionar Redis ou serviços de cache externos para gerenciamento de sessões ou blacklist de tokens.

## Decisions

### 1. Framework Web: FastAPI com Pydantic v2
- **Decisão**: Utilizar FastAPI para expor a API REST e Pydantic para validação e serialização de dados de entrada/saída.
- **Racional**: Suporte nativo a tipos Python 3.13, validação automática com schemas Pydantic, documentação interativa (OpenAPI/Swagger) gerada automaticamente e sistema idiomático de injeção de dependências (`Depends`) perfeito para autenticação de rotas.
- **Alternativas consideradas**: Flask (exigiria bibliotecas adicionais para OpenAPI, validação e injeção de dependências com mais boilerplate) ou aiohttp (menor ecossistema de extensões de segurança).
- **ADR**: Uma nova ADR (`docs/adr/0005-fastapi-e-jwt-auth.md`) deve formalizar a adoção do FastAPI e JWT para a API.

### 2. Persistência: SQLite com tabela `users` (ADR 0004)
- **Decisão**: Utilizar SQLite diretamente via driver padrão `sqlite3` (ou helper assíncrono simples) operando sobre o arquivo `db.sqlite3` na raiz do projeto.
- **Racional**: Cumpre a ADR 0004. Elimina a necessidade de subir containers de PostgreSQL ou MySQL para rodar a POC, mantendo os testes rápidos e execução local trivial.
- **Estrutura da tabela**:
  ```sql
  CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name VARCHAR(255) NOT NULL,
      username VARCHAR(100) UNIQUE NOT NULL,
      password VARCHAR(255) NOT NULL
  );
  ```
- **Alternativas consideradas**: ORM pesado (ex: SQLAlchemy com Alembic) — descartado temporariamente para manter a primeira entrega focada e sem complexidade desnecessária na camada de dados da POC.

### 3. Criptografia de Senha: Hashing com Bcrypt
- **Decisão**: Utilizar `passlib[bcrypt]` (ou biblioteca direta `bcrypt`) para gerar e verificar o hash das senhas com salt gerado automaticamente.
- **Racional**: Algoritmo resistente a ataques de dicionário e rainbow tables, adaptável via fator de trabalho. Impede o vazamento de credenciais caso o arquivo de banco seja exposto.
- **Alternativas consideradas**: SHA-256 simples (inseguro para senhas, vulnerável a força bruta rápida) e Argon2 (ótimo, mas bcrypt possui suporte e compatibilidade mais consolidada na stack Python).

### 4. Autenticação e Emissão de Token: PyJWT com padrão Bearer
- **Decisão**: Utilizar tokens JWT assinados com algoritmo simétrico HS256 contendo `sub` (username do usuário) e timestamp de expiração (`exp`).
- **Racional**: Arquitetura stateless. A validação de requisições protegidas não exige consulta ao banco a cada chamada para verificar se a sessão está ativa, tornando a proteção das rotas de predição altamente performática.
- **Alternativas consideradas**: Sessões baseadas em cookies/banco de dados (exigem consultas síncronas ao banco ou Redis a cada requisição, além de dificultar o consumo da API por clientes REST/scripts).

### 5. Arquitetura de Módulos em `src/player_modeling/api/`
- **Decisão**: Organizar a camada de API nos seguintes módulos internos:
  - `database.py`: gerenciamento de conexão e inicialização de schema SQLite (`init_db`).
  - `models.py` / `schemas.py`: esquemas Pydantic (`UserRegisterRequest`, `UserResponse`, `LoginRequest`, `TokenResponse`, `TokenData`).
  - `security.py`: utilitários de hash de senha (`hash_password`, `verify_password`), codificação/decodificação JWT (`create_access_token`, `decode_access_token`) e dependência FastAPI (`get_current_user`).
  - `routes/auth.py`: roteador com os endpoints `POST /auth/register` e `POST /auth/login`.
  - `app.py`: ponto de entrada da aplicação FastAPI agregando roteadores e middlewares.

### 6. Configurações e Variáveis de Ambiente
- **Decisão**: Centralizar variáveis de configuração (`JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, `DATABASE_PATH`) lidas via `os.getenv` ou Pydantic Settings, com documentação no `.env.example`.

## Risks / Trade-offs

- **[Revogação Imediata de Tokens JWT]** → Tokens stateless não podem ser revogados antes da expiração sem manter uma blacklist de tokens em memória/cache.
  - *Mitigação*: Definir tempo de expiração curto para o token (ex.: 30 minutos). Para o contexto da POC, essa janela atende com segurança aos requisitos sem necessidade de infraestrutura adicional (Redis).
- **[Concorrência de Escrita no SQLite]** → O SQLite bloqueia o banco durante operações de escrita concorrentes.
  - *Mitigação*: O fluxo de autenticação possui alta taxa de leitura e baixa taxa de escrita (apenas no registro). A abertura de conexões pontuais com timeout configurado ou uso de modo WAL é suficiente para mitigar contenção.
- **[Vazamento do Segredo JWT]** → Se a chave de assinatura for vazada ou fraca, tokens forjados podem ser criados.
  - *Mitigação*: Exigir chave via variável de ambiente, nunca commitar valores de produção e incluir chave forte de exemplo no `.env.example`.

## Migration Plan

1. Adicionar dependências no `pyproject.toml` (`fastapi`, `uvicorn`, `pyjwt`, `passlib`, `bcrypt`, `pydantic`).
2. Atualizar o arquivo `.env.example` com as novas variáveis (`JWT_SECRET_KEY`, `JWT_ALGORITHM`, etc.).
3. Executar rotina de migração/criação inicial da tabela `users` no SQLite (`init_db()`), executada no startup da aplicação FastAPI ou via script.
4. Validar o funcionamento com a nova suíte de testes em `src/tests/player_modeling/api/`.
