## Purpose

Fornecer endpoints de registro de usuários e autenticação com emissão de token JWT, além de dependência reutilizável de autorização para proteção de rotas restritas na API de modelagem de jogadores.

## ADDED Requirements

### Requirement: Registro de Usuários

A API DEVE (MUST) fornecer um endpoint `POST /auth/register` que permita cadastrar novos usuários, persistindo as informações na tabela `users` do banco SQLite (`db.sqlite3` na raiz) e aplicando hashing seguro na senha antes do armazenamento.

#### Scenario: Cadastro realizado com sucesso
- **WHEN** uma requisição POST válida for enviada para `/auth/register` contendo `name`, `username` válido (alinhado a IDs de jogadores, como `player_0000`) e `password`
- **THEN** a API deve criar um novo registro na tabela `users` com a senha criptografada via hash seguro (bcrypt), retornar status HTTP 201 Created e devolver os dados do usuário (`id`, `name`, `username`) sem exibir a senha.

#### Scenario: Tentativa de cadastro com username já existente
- **WHEN** uma requisição POST for enviada para `/auth/register` com um `username` que já se encontra cadastrado no banco de dados
- **THEN** a API deve rejeitar a criação do usuário e retornar status HTTP 409 Conflict com mensagem descritiva de erro.

#### Scenario: Validação de payload inválido no cadastro
- **WHEN** uma requisição POST for enviada para `/auth/register` omitindo campos obrigatórios ou com formato de payload inválido
- **THEN** a API deve recusar o processamento retornando status HTTP 422 Unprocessable Entity com detalhes dos erros de validação.

### Requirement: Autenticação e Emissão de Token JWT

A API DEVE (MUST) fornecer um endpoint `POST /auth/login` que valide as credenciais do usuário (`username` e `password`) e emita um JSON Web Token (JWT) assinado contendo o identificador do usuário e tempo de expiração determinado.

#### Scenario: Login com credenciais válidas
- **WHEN** uma requisição POST for enviada para `/auth/login` com `username` e `password` correspondentes a um usuário registrado e senha correta
- **THEN** a API deve retornar status HTTP 200 OK com payload contendo `access_token` (JWT válido assinado) e `token_type` com valor "bearer".

#### Scenario: Falha de autenticação com credenciais incorretas
- **WHEN** uma requisição POST for enviada para `/auth/login` com senha incorreta ou com `username` não registrado
- **THEN** a API deve recusar a autenticação retornando status HTTP 401 Unauthorized com mensagem informando que as credenciais são inválidas.

### Requirement: Proteção de Rotas da API via Bearer Token

A API DEVE (MUST) disponibilizar uma dependência de segurança reutilizável baseada em HTTP Bearer Token para interceptar requisições em rotas restritas e validar a autenticidade, assinatura e expiração do JWT recebido no cabeçalho Authorization.

#### Scenario: Acesso permitido a rota protegida com token válido
- **WHEN** uma requisição a um endpoint protegido incluir no cabeçalho `Authorization: Bearer <token>` um JWT válido, assinado com o segredo da aplicação e dentro do período de validade
- **THEN** a dependência de segurança deve permitir a execução do handler da rota, injetando as informações do usuário autenticado no contexto da requisição.

#### Scenario: Bloqueio imediato para requisição sem cabeçalho Authorization
- **WHEN** uma requisição a um endpoint protegido for enviada sem o cabeçalho `Authorization` ou sem o prefixo Bearer
- **THEN** a API deve rejeitar a requisição imediatamente com status HTTP 401 Unauthorized.

#### Scenario: Bloqueio para token JWT inválido ou corrompido
- **WHEN** uma requisição a um endpoint protegido apresentar um JWT com assinatura inválida, malformado ou adulterado
- **THEN** a API deve rejeitar a requisição imediatamente com status HTTP 401 Unauthorized.

#### Scenario: Bloqueio para token JWT expirado
- **WHEN** uma requisição a um endpoint protegido apresentar um JWT cuja data de expiração (`exp`) já tenha sido ultrapassada
- **THEN** a API deve rejeitar a requisição imediatamente com status HTTP 401 Unauthorized indicando token expirado.
