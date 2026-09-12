## 1. Schemas e Modelagem de Contrato

- [x] 1.1 Implementar o Enum `BartlePersona` e o schema `PersonaResponse` em `src/player_modeling/api/schemas.py`, verificando a validação e restrição dos quatro perfis com testes unitários em `src/tests/player_modeling/api/test_schemas.py`.

## 2. Endpoint de Inferência Mockado

- [x] 2.1 Implementar o roteador em `src/player_modeling/api/routes/players.py` com o endpoint `GET /players/{player_id}/persona`, aplicando proteção via `Depends(get_current_user)`, validação de regex `^player_\d{4,}$` no parâmetro `player_id` e retorno de resposta mockada/stub em conformidade com `PersonaResponse`.
- [x] 2.2 Conectar o roteador `players.router` à aplicação FastAPI em `src/player_modeling/api/app.py`, verificando o carregamento das rotas pelo aplicativo.

## 3. Testes Automatizados da Rota

- [x] 3.1 Criar a suíte de testes de integração em `src/tests/player_modeling/api/test_persona.py` cobrindo sucesso com Bearer Token válido (200 OK), rejeição por ausência/invalidade de token (401 Unauthorized) e rejeição de formato de `player_id` inválido (422 Unprocessable Entity).
- [x] 3.2 Executar a suíte de testes com `poetry run pytest src/tests/player_modeling/api/test_persona.py` e verificar aprovação completa.

## 4. Governança, Qualidade e Documentação

- [x] 4.1 Executar a suíte completa de testes (`poetry run pytest`), checagem estrita de tipos (`poetry run mypy .`) e linter (`poetry run ruff check .`), garantindo 100% de aprovação e conformidade com `disallow_untyped_defs = true`.
- [x] 4.2 Atualizar o `README.md` e o `CLAUDE.md` documentando o endpoint `GET /players/{player_id}/persona` e seu comportamento de stub, verificando o diff com `git diff`.
