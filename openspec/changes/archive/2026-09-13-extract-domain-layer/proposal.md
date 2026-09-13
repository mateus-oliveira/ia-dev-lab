## Why

A revisão arquitetural da atividade (`docs/aula6/etapa4-revisao-arquitetural.md`), feita sobre o
grafo real de imports do código, encontrou **quatro dependências apontando na direção errada**:

```text
ml/persona_model.py      ──> api/schemas.BartlePersona
worker/features.py       ──> simulator/events.EVENT_TYPES
worker/subscriber.py     ──> api/database.get_connection
alembic/env.py           ──> api/database.get_db_path
```

As quatro têm a mesma causa: **não existe uma camada de domínio**. Vocabulário do domínio (a
Taxonomia de Bartle, os tipos de evento, as colunas de feature) e infraestrutura compartilhada (a
conexão com o banco) foram parar no módulo que precisou deles primeiro, em vez de em um lugar comum.

Consequências concretas hoje:

* **`ml/` não pode ser usado sem FastAPI e Pydantic.** Um notebook de análise ou um job de batch
  scoring arrasta a camada web junto, porque `BartlePersona` mora em `api/schemas.py`.
* **O worker de produção depende do simulador.** O `CLAUDE.md` prevê "integração com fontes externas
  de eventos, como plataformas de jogos reais"; no dia em que os eventos vierem de um jogo real, o
  worker continuará importando `EVENT_TYPES` do gerador de dados sintéticos, ou o simulador terá que
  ser mantido vivo só para exportar uma lista de strings.
* **Worker e migrações dependem do pacote da API** para abrir uma conexão SQLite, sendo que nenhum
  dos dois fala HTTP.
* **A taxonomia está duplicada**: `PERSONAS = ["Achiever", "Explorer", "Socializer", "Killer"]` em
  `simulator/events.py` e o Enum `BartlePersona` em `api/schemas.py` descrevem o mesmo conjunto, sem
  nada garantindo que continuem iguais.

A decisão de corrigir agora, em vez de registrar como dívida, foi do desenvolvedor.

## What Changes

- **Nova camada `src/player_modeling/domain/`**, sem dependência de nenhum outro módulo do projeto:
  `personas.py` (Enum `BartlePersona` e a lista `PERSONAS` derivada dele), `events.py`
  (`EVENT_TYPES`) e `features.py` (`FEATURE_COLUMNS`, `LABEL_COLUMN`).
- **Nova camada `src/player_modeling/persistence/`** com `database.py`: `DEFAULT_DATABASE_PATH`,
  `get_db_path` e `get_connection`, movidos de `api/database.py`.
- **`api/database.py` reduzido** à dependency `get_db` do FastAPI, que é o único trecho realmente
  específico da API.
- **`api/schemas.py` importa `BartlePersona` do domínio** e a re-exporta, de modo que o contrato HTTP
  e todos os consumidores existentes continuem funcionando sem alteração.
- **Eliminação da duplicação da taxonomia**: `PERSONAS` passa a ser derivada de `BartlePersona`,
  preservando exatamente a ordem atual (`Achiever`, `Explorer`, `Socializer`, `Killer`), porque essa
  ordem influencia a geração determinística por semente do dataset sintético.
- **Imports atualizados** em `ml/`, `worker/`, `simulator/`, `alembic/env.py` e nos testes.
- **Fora de escopo**: qualquer mudança de comportamento, de contrato HTTP, de schema do banco ou dos
  arquivos de `src/data/`; extração de serviço (explicitamente rejeitada na revisão arquitetural);
  reorganização de `api/routes/`; qualquer alteração no modelo de ML.

## Capabilities

Refatoração pura: nenhuma capacidade de spec tem requisitos alterados. `skip_specs: true` no
`.openspec.yaml` desta change.

## Impact

- **Código**: novos `domain/` (4 arquivos) e `persistence/` (2 arquivos); `api/database.py`,
  `api/schemas.py`, `ml/persona_model.py`, `simulator/events.py`, `worker/features.py`,
  `worker/subscriber.py` e `alembic/env.py` passam a importar das novas camadas.
- **Testes**: imports atualizados em 8 arquivos de teste; novo `src/tests/player_modeling/domain/`
  garantindo que a camada de domínio não importe nenhum outro módulo do projeto.
- **Comportamento**: nenhum. Os 208 testes existentes são a rede da refatoração e devem permanecer
  verdes sem alteração de asserção.
- **Dependências**: nenhuma nova.
- **Documentação**: `README.md`, `CLAUDE.md` (árvore de diretórios e seção de organização) e nova
  ADR registrando a decisão.
