## 1. Configuração de Ambiente e Dependências

- [x] 1.1 Adicionar dependências (`fastapi`, `uvicorn`, `pyjwt`, `passlib[bcrypt]`, `pydantic`) no `pyproject.toml` via Poetry e verificar a instalação com `poetry install`.
- [x] 1.2 Atualizar o arquivo `.env.example` incluindo as variáveis de configuração JWT (`JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`) e caminho do banco SQLite (`DATABASE_PATH`), verificando a completude das variáveis documentadas.
- [x] 1.3 Criar a ADR 0005 (`docs/adr/0005-fastapi-e-jwt-auth.md`) documentando as decisões arquiteturais de adoção do FastAPI e JWT para autenticação, verificando a criação do documento.

## 2. Camada de Dados e Schemas (ADR 0004)

- [x] 2.1 Implementar módulo de gerenciamento do banco SQLite (`src/player_modeling/api/database.py`) com conexão e função `init_db()` para criar a tabela `users` (`id`, `name`, `username`, `password`) conforme ADR 0004, verificando a criação da tabela com teste unitário em `src/tests/player_modeling/api/test_database.py`.
- [x] 2.2 Implementar schemas Pydantic (`src/player_modeling/api/schemas.py`) para requisição e resposta de cadastro (`UserRegisterRequest`, `UserResponse`), login (`LoginRequest`) e token (`TokenResponse`), verificando regras de validação com testes em `src/tests/player_modeling/api/test_schemas.py`.

## 3. Segurança e Criptografia

- [x] 3.1 Implementar utilitários de hashing de senha (`hash_password`, `verify_password`) com bcrypt e geração/validação de JWT (`create_access_token`, `decode_access_token`) em `src/player_modeling/api/security.py`, verificando comportamento com testes em `src/tests/player_modeling/api/test_security.py`.
- [x] 3.2 Implementar a dependência FastAPI injetável `get_current_user` em `src/player_modeling/api/security.py` para extrair e validar o Bearer Token do cabeçalho `Authorization`, retornando 401 Unauthorized para tokens ausentes, corrompidos ou expirados, verificando com testes em `src/tests/player_modeling/api/test_security_dependency.py`.

## 4. Endpoints e Proteção de Rotas

- [x] 4.1 Implementar endpoint `POST /auth/register` em `src/player_modeling/api/routes/auth.py` persistindo o novo usuário com senha hasheada e retornando HTTP 201 Created (ou HTTP 409 Conflict se username duplicado), verificando com testes em `src/tests/player_modeling/api/test_register.py`.
- [x] 4.2 Implementar endpoint `POST /auth/login` em `src/player_modeling/api/routes/auth.py` validando credenciais no SQLite e retornando o token JWT com HTTP 200 OK (ou HTTP 401 Unauthorized para credenciais inválidas), verificando com testes em `src/tests/player_modeling/api/test_login.py`.
- [x] 4.3 Configurar o app FastAPI em `src/player_modeling/api/app.py` integrando os roteadores de autenticação e adicionando uma rota protegida de teste (`GET /auth/me` ou similar) com `Depends(get_current_user)`, verificando a proteção com testes em `src/tests/player_modeling/api/test_protected_routes.py`.

## 5. Validação de Qualidade e Documentação

- [x] 5.1 Executar a suíte completa de testes da API via `poetry run pytest src/tests/player_modeling/api/` e verificar 100% de sucesso.
- [x] 5.2 Executar a checagem estrita de tipos com `poetry run mypy .` e análise de lint com `poetry run ruff check .`, verificando conformidade total com `disallow_untyped_defs = true`.
- [x] 5.3 Atualizar documentação em `README.md` e `CLAUDE.md` com os novos comandos de execução da API e detalhes das rotas de autenticação, verificando as alterações via `git diff`.
