# ADR 0005 - Adoção de FastAPI e Autenticação JWT

* **Status:** Aceito
* **Data:** 2026-09-11
* **Decisão:** Adoção de FastAPI como framework web da API e PyJWT/Bcrypt para autenticação e autorização stateless via Bearer Token.

## Contexto

O escopo inicial do projeto (`CLAUDE.md` e `docs/escopo.md`) previa a entrega de um endpoint GET de predição de perfil sem camada de autenticação/autorização na primeira versão. Contudo, a equipe autorizou explicitamente a inclusão desta camada de segurança na API (`src/player_modeling/api/`), sobrepondo a restrição inicial do `config.yaml` e complementando a [ADR 0004](0004-db-e-primeira-tabela-users.md), que já estabeleceu a tabela `users` no banco SQLite (`db.sqlite3` na raiz).

Para atender aos requisitos de registro de usuários (`POST /auth/register`), login (`POST /auth/login`) e proteção de endpoints restritos por Bearer Token, foi necessário padronizar o framework web, os mecanismos criptográficos de senha e o protocolo de autenticação.

## Decisões

### 1. Framework Web: FastAPI
Adotado **FastAPI** (com servidor ASGI **Uvicorn** e **Pydantic v2**) para a camada de API em `src/player_modeling/api/`:
- **Tipagem nativa**: Total compatibilidade com Python 3.13 e validação estrita no MyPy (`disallow_untyped_defs = true`).
- **Injeção de dependências**: Sistema idiomático (`Depends`) para interceptar requisições e validar credenciais / tokens JWT sem boilerplate de middlewares manuais.
- **OpenAPI**: Geração automática de documentação interativa (`/docs` e `/redoc`).

### 2. Criptografia de Senhas: Bcrypt
As senhas de usuários são tratadas com **Bcrypt** com salt aleatório:
- Nenhuma senha é persistida em texto plano.
- O hash gerado é armazenado no campo `password` da tabela `users` do SQLite conforme ADR 0004.

### 3. Autenticação e Autorização: JWT (JSON Web Token) com Padrão Bearer
Adotado **PyJWT** com algoritmo simétrico **HS256**:
- **Stateless**: A validação das rotas protegidas não exige consultas síncronas de sessão a banco de dados ou cache externo (como Redis, que permanece fora de escopo).
- **Payload**: Contém `sub` (username ou ID do usuário) e `exp` (timestamp de expiração com tempo de vida limitado, padrão de 30 minutos).
- **Tratamento de erro**: Requisições sem token, com assinatura adulterada ou expiradas retornam imediatamente código HTTP 401 Unauthorized.

### 4. Configuração de Variáveis de Ambiente
As configurações sensíveis são injetadas exclusivamente via variáveis de ambiente, com defaults seguros para desenvolvimento documentados em `.env.example`:
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- `DATABASE_PATH`

## Consequências

- **Positivas**:
  - API moderna, performática e tipada.
  - Segurança de credenciais e proteção das rotas de modelagem sem necessidade de infraestrutura pesada externa.
  - Testes rápidos e isolados que podem ser executados com `TestClient` em memória ou SQLite em arquivo temporário.
- **Negativas / Limitações**:
  - Revogação imediata de token antes da expiração natural (`exp`) exigiria uma lista de revogação/blacklist, dispensada na POC atual por adicionar dependência de cache.
