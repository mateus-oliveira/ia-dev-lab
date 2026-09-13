# Etapa 4 — Revisão arquitetural com apoio de IA

Levantamento feito sobre o código real (`grep` dos imports internos, contagem de linhas por
módulo, pontos de entrada e schema do banco), não sobre a documentação do projeto.

## 1. Resumo da arquitetura atual

### Tamanho

| | Linhas | Arquivos |
|---|---:|---:|
| Produção (`src/player_modeling/`) | 2.009 | 24 |
| Testes (`src/tests/`) | 2.801 | 21 |
| Harness (`scripts/`) | 622 | 6 |

Por módulo de produção: `api/` 598, `ml/` 436, `simulator/` 382, `scripts/` 313, `worker/` 279.

### Pontos de entrada (3 processos independentes)

| Processo | Entrada | Papel |
|---|---|---|
| API | `api/app.py` (`uvicorn`) | HTTP: autenticação e consulta de perfil |
| Publisher | `simulator/publisher.py` (`python -m`) | cronjob: gera eventos sintéticos → RabbitMQ |
| Subscriber | `worker/subscriber.py` (`python -m`) | cronjob: RabbitMQ → features → SQLite |

Mais dois scripts de uso manual: `scripts/generate_raw_events.py` (gera o dataset de treino) e
`scripts/evaluate_model.py` (avalia os modelos).

### Estado compartilhado

Um único SQLite (`db.sqlite3`, schema por Alembic) com `users` e `player_features`, e uma fila
RabbitMQ entre publisher e subscriber. Os três processos se comunicam **apenas** por esses dois
recursos — não há chamada direta entre eles.

### Grafo de dependências entre módulos

```text
     scripts/ ──────────────┬──────────────┐
        │                   │              │
        v                   v              v
      ml/ ───────────> api/schemas    simulator/  <──┐
        │                   ^                        │
        │                   │                        │
     persona_model          │                   worker/features
        ^                   │                        ^
        │                   │                        │
   knn, decision_tree   api/routes            worker/subscriber
                            ^                        │
                            │                        v
                          api/app              api/database
```

Direção esperada em uma arquitetura em camadas: `api/` → `ml/` → domínio, e `worker/` → domínio.
Três arestas apontam para o lado errado.

## 2. Pontos de acoplamento encontrados

### A. `ml/persona_model.py` → `api/schemas.BartlePersona` (dependência invertida)

```python
# src/player_modeling/ml/persona_model.py:26
from player_modeling.api.schemas import BartlePersona
```

O módulo de Machine Learning importa do módulo de API. A Taxonomia de Bartle — que é **o vocabulário
central do domínio de Player Modeling**, anterior a qualquer decisão sobre HTTP — está declarada
dentro do arquivo de schemas Pydantic de serialização da API.

Consequência concreta: hoje é impossível usar `ml/` sem carregar FastAPI e Pydantic. Um notebook de
análise, um job de batch scoring ou um segundo consumidor do modelo arrastam a camada web junto.

### B. `worker/features.py` → `simulator/events.EVENT_TYPES` (dependência invertida)

```python
# src/player_modeling/worker/features.py:11
from player_modeling.simulator.events import EVENT_TYPES
```

O ETL depende do **simulador**. Os tipos de evento (`attack`, `explore_area`, `chat`, `trade`,
`quest_complete`, `retry`) são vocabulário do domínio, não propriedade de quem gera os dados
sintéticos.

Consequência concreta, e esta é a mais séria: o `CLAUDE.md` prevê "integração com fontes externas de
eventos, como plataformas de jogos reais". No dia em que os eventos vierem de um jogo de verdade, o
worker de produção continuará importando do simulador — ou o simulador terá que ser mantido vivo só
para exportar uma tupla de strings.

### C. `worker/subscriber.py` → `api/database.get_connection` (camada errada)

```python
# src/player_modeling/worker/subscriber.py:20
from player_modeling.api.database import get_connection
```

O worker é um cronjob que não fala HTTP, mas depende do pacote `api/` para abrir conexão com o
banco. O acesso a dados foi parar dentro de `api/` por acidente histórico: a API foi o primeiro
módulo a precisar dele (ADR 0004).

Consequência concreta: subir o worker exige o pacote inteiro da API instalado, e qualquer mudança na
forma como a API gerencia conexões afeta um processo que não tem nada a ver com a API.

### D. Acoplamentos legítimos (não são problema)

* `scripts/generate_raw_events.py` → `simulator/` + `worker/features`: é um script de composição,
  o lugar certo para juntar duas partes.
* `knn.py`/`decision_tree.py` → `persona_model.py`: a direção correta, criada na Etapa 2.
* `api/routes/` → `ml/persona_model`: correta — a camada de entrega depende do modelo.

### O padrão por trás dos três problemas

Não são três defeitos independentes. **Não existe uma camada de domínio.** Vocabulário do domínio
(`BartlePersona`, `EVENT_TYPES`) e infraestrutura compartilhada (conexão com o banco) foram parar no
módulo que precisou deles primeiro. Cada um sozinho é um import inofensivo; juntos, produzem um grafo
em que `ml/`, `worker/` e `api/` dependem uns dos outros em ciclo conceitual.

## 3. Decisão: mais modular, extrair um serviço, ou tamanho certo?

**Decisão: o projeto está no tamanho certo como unidade de implantação, e precisa de mais
modularidade interna. Nenhum serviço deve ser extraído.**

### Por que NÃO extrair um serviço

Aplicando os critérios de quando extrair um serviço:

| Critério | Situação real |
|---|---|
| Escala independente entre partes | Não existe. 2.009 linhas, 1000 linhas de dataset, 2 jogadores de teste, SQLite em arquivo. |
| Times independentes | Não existe. Dois autores, um repositório, uma branch por tarefa. |
| Ciclo de release independente | Não existe. Tudo versionado e mergeado junto (ADR 0002). |
| Fronteira tecnológica | Não existe. Tudo Python 3.13, mesmo `poetry install`. |
| Isolamento de falha | Já existe **sem** rede: os três processos já são independentes, acoplados só por fila e banco. |

O candidato mais óbvio seria um serviço de inferência (`ml/` atrás de HTTP). Ele custaria: um
protocolo de rede, serialização, versionamento de contrato, um segundo deploy, latência por
requisição e tratamento de indisponibilidade — em troca de um isolamento que o projeto **já tem** de
graça, porque `ml/` é importado como biblioteca por um único processo.

Pior: extrair serviço agora **congelaria** o problema real. A dependência `ml/ → api/schemas`
atravessaria a fronteira de rede, e os dois lados precisariam concordar sobre `BartlePersona` sem
que exista um lugar comum onde ela esteja definida. Extrair um serviço antes de resolver o
acoplamento interno transforma um import ruim em um contrato distribuído ruim.

### Por que SIM mais modularidade interna

Os três acoplamentos da seção 2 têm a mesma causa e a mesma correção: **criar uma camada de
domínio** (`src/player_modeling/domain/`) que não dependa de nada e da qual todos dependam.

```text
ANTES                              DEPOIS
  ml/ ──────> api/schemas            ml/ ─────┐
  worker/ ──> simulator/             worker/ ─┼──> domain/
  worker/ ──> api/database           api/ ────┘
                                     simulator/ ┘
```

Conteúdo mínimo de `domain/`: `BartlePersona` (taxonomia), `EVENT_TYPES` e `FEATURE_COLUMNS`
(vocabulário de eventos e features), e a conexão com o banco movida de `api/database.py` para uma
camada de persistência compartilhada.

Custo: baixo — são movimentações de declaração com 208 testes como rede, no mesmo padrão do REFACTOR
já feito em `ml/` na Etapa 2. `api/schemas.py` continua importando `BartlePersona` do domínio e
re-exportando para os schemas Pydantic, então o contrato HTTP não muda.

Ganho: `ml/` deixa de arrastar FastAPI; o worker deixa de depender do simulador, destravando a
integração com fontes externas de eventos já prevista no `CLAUDE.md`; e o grafo de dependências
passa a ter uma direção única.

### Nota sobre o papel da IA nesta análise

O agente produziu o levantamento (grafo de imports, métricas, identificação das três arestas
invertidas) e a recomendação. O critério de decisão — *não* extrair serviço — foi validado contra
os critérios vistos em aula, não contra preferência. A decisão de implementar a camada de domínio
agora ou registrá-la como dívida assumida é do desenvolvedor, e está registrada na ADR da Etapa 5.
