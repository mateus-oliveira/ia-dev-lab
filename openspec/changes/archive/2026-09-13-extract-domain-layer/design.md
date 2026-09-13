## Context

O projeto organiza `src/player_modeling/` por domínio funcional (`api/`, `ml/`, `simulator/`,
`worker/`, `scripts/`), conforme o `CLAUDE.md`. O que falta não é uma sexta divisão funcional, e sim
uma camada **transversal**: o vocabulário que todas as outras usam.

## Goals / Non-Goals

**Goals:**
- Fazer o grafo de dependências internas apontar em uma única direção.
- Permitir usar `ml/` sem carregar FastAPI, e `worker/` sem carregar `api/` nem `simulator/`.
- Eliminar a duplicação da Taxonomia de Bartle entre `simulator/events.py` e `api/schemas.py`.
- Não alterar nenhum comportamento observável.

**Non-Goals:**
- Não é objetivo extrair serviço (rejeitado na revisão arquitetural por ausência de escala, times
  ou ciclos de release independentes).
- Não é objetivo introduzir um ORM, repositórios genéricos ou camada de aplicação.
- Não é objetivo mover a lógica de negócio dos módulos atuais para `domain/` — só o vocabulário e os
  contratos de dados vão para lá.

## Decisions

### `domain/` contém vocabulário, não comportamento

Entram em `domain/` apenas declarações que descrevem *o que as coisas são* no domínio de Player
Modeling: a taxonomia, os tipos de evento, as colunas de feature. Não entram: geração de eventos
(fica em `simulator/`), agregação de features (fica em `worker/`), treino e inferência (ficam em
`ml/`). O critério é verificável: **`domain/` não importa nada de `player_modeling`**, e existe um
teste que falha se isso mudar.

Alternativa considerada: um `shared/` ou `common/` de uso geral. Rejeitada — nomes assim atraem
qualquer coisa que não tenha lugar óbvio e viram depósito. `domain/` tem critério de entrada.

### `persistence/` separado de `domain/`

A conexão com o banco é infraestrutura, não domínio: ela conhece `sqlite3` e variáveis de ambiente.
Misturá-la em `domain/` quebraria a própria regra "não depende de nada" logo na primeira semana.
Daí duas camadas e não uma.

`get_db` (o generator usado como dependency do FastAPI) **fica** em `api/database.py`: é um detalhe
do framework web, não de persistência. É o único trecho do arquivo original que era realmente da API.

### `PERSONAS` derivada de `BartlePersona`, com ordem preservada

`simulator/events.py` declara `PERSONAS = ["Achiever", "Explorer", "Socializer", "Killer"]`, a mesma
informação do Enum `BartlePersona`. A lista passa a ser derivada do Enum.

A ordem é preservada **exatamente**, e isso é deliberado: `generate_raw_events.py` sorteia personas
com `random` semeado, então a ordem da lista influencia qual jogador recebe qual persona para uma
dada semente. Alterá-la mudaria o dataset gerado por `--seed 42` — e o `CLAUDE.md` proíbe
sobrescrever `src/data/`. Por isso o Enum é declarado na ordem da lista atual, e não em ordem
alfabética, com um teste garantindo que o conjunto de valores coincide.

### `api/schemas.py` re-exporta `BartlePersona`

Em vez de atualizar todos os consumidores de `api.schemas.BartlePersona`, o schema passa a importá-la
do domínio e a re-exportá-la via `__all__`. Motivo: `BartlePersona` **é** parte do contrato HTTP (é o
tipo de dois campos de `PersonaResponse`), então continuar visível em `api/schemas.py` é correto, não
é um atalho de compatibilidade. A fonte da verdade passa a ser única.

### A refatoração não altera nenhum teste de comportamento

Os 208 testes existentes são a rede. Apenas linhas de `import` mudam nos testes; nenhuma asserção é
tocada. Se alguma asserção precisar mudar, a refatoração deixou de ser refatoração.

## Risks / Trade-offs

- **Mais um nível de indireção**: quem lê `ml/persona_model.py` precisa de um salto a mais para achar
  a definição de `BartlePersona`. Aceito — é o custo de ter fonte única.
- **Risco de `domain/` virar depósito** com o tempo. Mitigado pelo teste que proíbe imports internos.
- **Churn de imports** em 15+ arquivos em um único commit, o que polui o diff. Aceito: dividir em
  vários commits deixaria o repositório em estado inconsistente no meio.

## Migration Plan

Refatoração interna, sem migração de dados, schema ou contrato. `alembic/env.py` passa a importar de
`persistence/`, sem efeito sobre revisões já aplicadas.

## Open Questions

Nenhuma.
