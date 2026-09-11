## Why

O item 3 do escopo inicial da POC (`CLAUDE.md` e `docs/escopo.md`) estabelece a disponibilização de um endpoint GET que retorne o perfil do jogador classificado segundo a Taxonomia de Bartle (`Killer`, `Achiever`, `Socializer`, `Explorer`).

Esta mudança implementa o contrato HTTP definitivo desse serviço (`GET /players/{player_id}/persona`) utilizando uma abordagem de **stub/mock**. Isso viabiliza a validação imediata da integração por clientes e a proteção por autenticação JWT antes que a pipeline completa de dados e o modelo de ML em disco estejam finalizados.

## What Changes

- **Novo Endpoint de Predição**: Criação do endpoint `GET /players/{player_id}/persona` em `src/player_modeling/api/routes/players.py` (ou integrado ao router da API).
- **Proteção de Rota por Token**: Aplicação da dependência reutilizável `Depends(get_current_user)` (desenvolvida na change `auth-endpoints`), exigindo Bearer Token JWT válido para acesso e retornando HTTP 401 Unauthorized em caso de token inválido ou ausente.
- **Validação de Entrada (`player_id`)**: Validação do identificador do jogador via Pydantic/FastAPI `Path` com padrão regex `^player_\d{4,}$`, rejeitando parâmetros fora do formato com HTTP 422 Unprocessable Entity.
- **Contrato de Resposta e Enum da Taxonomia de Bartle**: Criação do schema `PersonaResponse` e do Enum `BartlePersona` contendo estritamente os perfis `Killer`, `Achiever`, `Socializer` e `Explorer`.
- **Resposta Mockada (Stub)**: Retorno direto de perfil mockado (estratégia leve determinística ou pseudo-aleatória), sem dependência de Pandas, scikit-learn ou leitura de arquivos em `src/data/`.
- **Registro no FastAPI**: Inclusão do novo roteador no `src/player_modeling/api/app.py`.
- **Espelhamento de Testes**: Implementação de testes em `src/tests/player_modeling/api/test_persona.py` cobrindo autenticação, validação de rota e contrato de dados retornado.
- **Fora de Escopo**:
  - Treinamento, inferência ou carregamento de modelos reais de Machine Learning.
  - Leitura ou manipulação dos datasets em `src/data/` (`events.csv`, `sessions_features.csv`).
  - Ingestão via RabbitMQ ou processamento via Worker ETL.
  - Criação de interface gráfica (frontend).

## Capabilities

### New Capabilities
- `inference-endpoint`: Rota protegida `GET /players/{player_id}/persona` com validação de entrada e retorno mockado do perfil de jogador na Taxonomia de Bartle.

### Modified Capabilities
<!-- Nenhuma capacidade existente modificada -->

## Impact

- **Código**: Novos schemas em `src/player_modeling/api/schemas.py`, novas rotas em `src/player_modeling/api/routes/players.py` e registro no `src/player_modeling/api/app.py`.
- **Dependências**: Nenhuma nova dependência adicionada ao `pyproject.toml` (utiliza os recursos existentes do FastAPI e Pydantic).
- **Dados**: Zero alteração em `src/data/`.
- **Governança**: 100% de conformidade mantida com `disallow_untyped_defs = true` no MyPy e regras do Ruff.
