## Why

A API do Player Modeling Lab precisa proteger seus serviços de predição e dados sensíveis contra acesso não autorizado, além de viabilizar a gestão segura de identidades de jogadores. Esta mudança introduz os mecanismos fundamentais de autenticação, cadastro e proteção de rotas na API (`src/player_modeling/api/`).

**Justificativa de Escopo**: O `openspec/config.yaml` e o `CLAUDE.md` estabeleciam inicialmente que a primeira versão do projeto não conteria autenticação/autorização. No entanto, a equipe autorizou explicitamente a antecipação e inclusão desta camada de segurança na API, sobrepondo formalmente a restrição inicial do `config.yaml`, amparada pela definição da tabela `users` e banco SQLite registrada na ADR 0004.

## What Changes

- **Registro de Usuários (ADR 0004)**: Criação do endpoint `POST /auth/register` que recebe credenciais (`name`, `username` alinhado ao padrão de IDs de jogadores como `player_0000`, e `password`), persiste os dados na tabela `users` do SQLite (`db.sqlite3` na raiz) e aplica hashing criptográfico seguro (bcrypt) na senha, impedindo armazenamento em texto plano.
- **Autenticação e Emissão de Token JWT**: Criação do endpoint `POST /auth/login` que autentica o usuário via `username` e `password`, validando a senha hasheada e emitindo um JSON Web Token (JWT) assinado com tempo de expiração configurável.
- **Proteção de Rotas com Bearer Token**: Criação de dependência injetável/reutilizável de segurança (FastAPI `Depends`) para interceptar requisições em endpoints protegidos, validando a assinatura, estrutura e expiração do Bearer Token e retornando imediatamente erro HTTP 401 Unauthorized caso o token seja inválido ou ausente.
- **Configuração de Ambiente e Harness**: Especificação das dependências necessárias no `pyproject.toml` via Poetry (`fastapi`, `pyjwt`, `passlib[bcrypt]`/`bcrypt`, `pydantic`) e mapeamento das variáveis de configuração JWT (`JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`) e de banco de dados no `.env.example`.
- **Espelhamento de Testes**: Implementação de testes unitários e de integração alocados estritamente em `src/tests/player_modeling/api/` para cobrir registro, login, validação de tokens e rejeição de requisições não autorizadas.
- **Fora de Escopo**:
  - Nenhuma interface visual (frontend) será desenvolvida (conforme seção "Não fazer" do `CLAUDE.md`).
  - Os datasets em `src/data/` (`events.csv`, `sessions_features.csv`) permanecem intactos e não serão alterados.
  - O `mypy` continuará exigindo tipagem estrita (`disallow_untyped_defs = true`) em todo o código adicionado.

## Capabilities

### New Capabilities
- `auth-endpoints`: Endpoints de cadastro (`POST /auth/register`), autenticação com emissão de JWT (`POST /auth/login`) e dependência de autorização via Bearer Token para proteção de rotas da API.

### Modified Capabilities
<!-- Nenhuma capacidade existente modificada -->

## Impact

- **Código**: Novos módulos na camada de API (`src/player_modeling/api/`) contendo rotas de autenticação, esquemas Pydantic, utilitários de hashing/JWT e conexão com o banco SQLite.
- **Dependências (`pyproject.toml`)**: Inclusão de `fastapi`, `pyjwt`, `passlib`, `bcrypt`, `pydantic`.
- **Configurações (`.env.example`)**: Inclusão de chaves secretas e parâmetros de expiração de token JWT.
- **Banco de Dados**: Criação e gestão da tabela `users` no `db.sqlite3` na raiz do projeto (ignorado no `.gitignore` conforme ADR 0004).
- **Testes**: Nova suíte de testes em `src/tests/player_modeling/api/`.
