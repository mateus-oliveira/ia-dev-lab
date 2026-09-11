## Context

Ver `proposal.md` para motivação e escopo da funcionalidade.
O projeto possui uma infraestrutura de API baseada em FastAPI configurada em `src/player_modeling/api/`, com autenticação JWT e segurança Bearer formalizadas na [ADR 0005](file:///c:/Users/ander/Documents/ia-dev-lab/docs/adr/0005-fastapi-e-jwt-auth.md) e [ADR 0004](file:///c:/Users/ander/Documents/ia-dev-lab/docs/adr/0004-db-e-primeira-tabela-users.md).

O item 3 do objetivo inicial (`CLAUDE.md` e `docs/escopo.md`) requer um endpoint GET que retorne o perfil do jogador classificado segundo a Taxonomia de Bartle (`Killer`, `Achiever`, `Socializer`, `Explorer`). Esta change estabelece a interface desse serviço antecipadamente por meio de uma abordagem "contract-first" com stubs.

## Goals / Non-Goals

**Goals:**
- Implementar o endpoint `GET /players/{player_id}/persona` na API FastAPI, protegido obrigatoriamente por `Depends(get_current_user)`.
- Validar estritamente o parâmetro de caminho `player_id` com regex `^player_\d{4,}$`.
- Definir o contrato formal de dados de saída através de schema Pydantic (`PersonaResponse`) e Enum tipado (`BartlePersona`).
- Utilizar uma implementação mock/stub leve em memória, sem acoplamento a modelos de Machine Learning ou acesso a disco.
- Adicionar cobertura de testes unitários e de integração em `src/tests/player_modeling/api/test_persona.py`.
- Manter tipagem estrita com MyPy (`disallow_untyped_defs = true`) e lint com Ruff.

**Non-Goals:**
- Carregar ou executar modelos treinados de scikit-learn ou inferência estatística.
- Ler, modificar ou depender dos arquivos em `src/data/` (`events.csv`, `sessions_features.csv`).
- Implementar filas RabbitMQ ou rotinas de ETL do Worker.
- Desenvolver interface de frontend.

## Decisions

### 1. Abordagem de Stub / Mock para Validação Contratual Antecipada
- **Decisão:** Implementar a resolução da persona como um stub determinístico em memória.
- **Racional:** Adotar a prática de desenvolvimento orientado a contratos (contract-first). Permite que os consumidores da API e a suíte de testes de integração comecem a utilizar e validar o endpoint imediatamente, antes que a pipeline completa (simulador -> fila -> ETL -> modelo treinado) esteja disponível.
- **Alternativas consideradas:**
  - *Carregar modelo real `.pkl` pré-treinado*: Descartado neste momento por adicionar dependência pesada de scikit-learn e requerer pipeline de extração de features em tempo real que ainda não foi implementada.
  - *Ler diretamente `src/data/sessions_features.csv`*: Descartado para respeitar a regra fundamental do projeto de nunca ler/escrever diretamente os dados brutos sintéticos a partir da camada de API.

### 2. Modelagem do Contrato com Enum `BartlePersona`
- **Decisão:** Criar um Enum tipado (`str, Enum` ou `StrEnum`) com os 4 arquétipos exatos da taxonomia:
  ```python
  class BartlePersona(str, Enum):
      KILLER = "Killer"
      ACHIEVER = "Achiever"
      SOCIALIZER = "Socializer"
      EXPLORER = "Explorer"
  ```
- **Racional:** Garante que a OpenAPI documente os valores possíveis, que o Pydantic valide estritamente a serialização e que o type-checker detecte qualquer divergência em tempo de compilação.
- **Alternativas consideradas:** Campo `persona: str` genérico (rejeitado por não impor restrição de domínio na documentação e validação).

### 3. Estratégia de Geração do Stub
- **Decisão:** Mapear o `player_id` para um perfil de forma determinística utilizando uma função hash simples sobre o identificador (ex.: `list(BartlePersona)[hash(player_id) % 4]`).
- **Racional:**
  - Respostas determinísticas e consistentes para um mesmo jogador (ex: `player_0000` sempre retorna o mesmo perfil durante os testes).
  - Distribuição realista entre diferentes perfis para diferentes IDs, sem necessidade de estado mutável.
  - Testes unitários totalmente previsíveis e reproduzíveis.

### 4. Modularização da API
- **Decisão:** Criar o roteador em `src/player_modeling/api/routes/players.py` com prefixo `/players`, registrando-o no `src/player_modeling/api/app.py`.
- **Racional:** Mantém a organização por domínio da API coesa, separando rotas de gerenciamento de jogadores/predição das rotas de autenticação (`routes/auth.py`).

## Risks / Trade-offs

- **[Risco: Divergência entre Contrato Mockado e Futura Saída do Modelo de ML]**
  - *Mitigação*: O schema `PersonaResponse` adota os nomes literais dos perfis idênticos à coluna `true_persona` de `src/data/sessions_features.csv`, garantindo total compatibilidade quando o classificador real for plugado.
- **[Risco: Clientes suporem que a resposta atual reflete inferência real de ML]**
  - *Mitigação*: Documentar explicitamente no campo `description` da rota OpenAPI que o endpoint opera temporariamente com stub para fins de validação contratual.

## Migration Plan

1. Definir os schemas e o Enum em `src/player_modeling/api/schemas.py`.
2. Criar a rota protegida em `src/player_modeling/api/routes/players.py`.
3. Conectar o roteador à aplicação FastAPI em `src/player_modeling/api/app.py`.
4. Implementar a suíte de testes em `src/tests/player_modeling/api/test_persona.py`.
5. Validar lint, tipagem e testes com o harness.
