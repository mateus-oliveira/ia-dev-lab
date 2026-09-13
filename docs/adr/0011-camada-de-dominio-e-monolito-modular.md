# ADR 0011 - Camada de Domínio e Monólito Modular

* **Status:** Aceito
* **Data:** 2026-09-13
* **Decisão:** Manter o projeto como uma única unidade de implantação (nenhum serviço extraído) e corrigir o acoplamento interno com uma camada de domínio e uma camada de persistência compartilhadas.

## Contexto

Uma revisão arquitetural feita sobre o código real — grafo de imports internos, contagem de linhas por módulo, pontos de entrada e schema do banco, registrada em `docs/aula6/etapa4-revisao-arquitetural.md` — encontrou quatro dependências apontando na direção errada:

```text
ml/persona_model.py      ──> api/schemas.BartlePersona
worker/features.py       ──> simulator/events.EVENT_TYPES
worker/subscriber.py     ──> api/database.get_connection
alembic/env.py           ──> api/database.get_db_path
```

As quatro tinham a mesma causa: **não existia camada de domínio**. O vocabulário do domínio de Player Modeling (a Taxonomia de Bartle, os tipos de evento, as colunas de feature) e a infraestrutura compartilhada (a conexão com o banco) foram declarados dentro do módulo que precisou deles primeiro. Cada import isolado era inofensivo; juntos produziam um grafo em que `ml/`, `worker/`, `api/` e as migrações dependiam uns dos outros em ciclo conceitual.

Os efeitos eram concretos, não estéticos:

* `ml/` não podia ser usado sem carregar FastAPI e Pydantic, porque `BartlePersona` morava em `api/schemas.py` — qualquer notebook de análise ou job de batch scoring arrastaria a camada web junto;
* o worker de produção dependia do **simulador** para conhecer os tipos de evento, o que colidiria diretamente com a "integração com fontes externas de eventos, como plataformas de jogos reais" prevista na evolução planejada do `CLAUDE.md`;
* worker e migrações Alembic exigiam o pacote da API instalado só para abrir uma conexão SQLite, sendo que nenhum dos dois fala HTTP;
* a Taxonomia de Bartle estava **duplicada** — `PERSONAS = ["Achiever", "Explorer", "Socializer", "Killer"]` em `simulator/events.py` e o Enum `BartlePersona` em `api/schemas.py` — sem nada garantindo que continuassem iguais.

O projeto, nesse momento, tinha 2.009 linhas de produção, 2.801 de teste, três processos (API, publisher, subscriber) acoplados apenas por uma fila RabbitMQ e um arquivo SQLite, e dois autores trabalhando no mesmo repositório.

## Decisão

### O projeto permanece uma única unidade de implantação

**Nenhum serviço será extraído.** O candidato mais óbvio — expor `ml/` como serviço de inferência atrás de HTTP — foi avaliado e rejeitado.

### Camada de domínio (`src/player_modeling/domain/`)

Criada uma camada transversal que declara o vocabulário do domínio e **não importa nenhum outro módulo de `player_modeling`**:

* `personas.py` — Enum `BartlePersona` e a lista `PERSONAS` derivada dele;
* `events.py` — `EVENT_TYPES`;
* `features.py` — `FEATURE_COLUMNS` e `LABEL_COLUMN`.

O critério de entrada é verificável, não uma convenção: `src/tests/player_modeling/domain/test_domain_layer.py` analisa a AST de cada módulo do pacote e falha se qualquer import interno aparecer.

Entra em `domain/` apenas declaração de vocabulário e contrato de dados. Comportamento continua no módulo funcional correspondente: geração de eventos em `simulator/`, agregação de features em `worker/`, treino e inferência em `ml/`.

### Camada de persistência (`src/player_modeling/persistence/`)

`DEFAULT_DATABASE_PATH`, `get_db_path` e `get_connection` movidos de `api/database.py` para `persistence/database.py`. `api/database.py` fica apenas com `get_db`, o generator usado como dependency do FastAPI — a única parte do arquivo original que era de fato específica da API.

Persistência é separada de domínio de propósito: ela conhece `sqlite3` e variáveis de ambiente, e colocá-la em `domain/` quebraria a regra "não depende de nada" logo na primeira semana.

### `api/schemas.py` re-exporta `BartlePersona`

O schema passa a importar `BartlePersona` do domínio e a re-exportá-la via `__all__`. Isso não é um atalho de compatibilidade: `BartlePersona` **é** parte do contrato HTTP (tipa dois campos de `PersonaResponse`), então continuar visível em `api/schemas.py` é correto. O que muda é que a fonte da verdade passa a ser única.

### Ordem de `BartlePersona` congelada

O Enum é declarado na ordem `Achiever, Explorer, Socializer, Killer` — não em ordem alfabética — porque `PERSONAS` é derivada dele e alimenta o sorteio semeado de `generate_raw_events.py`. Reordenar mudaria o dataset produzido por `--seed 42`, e `src/data/` não pode ser sobrescrito (regra "Não modificar dados brutos" do `CLAUDE.md`). Há teste específico protegendo essa ordem.

## Justificativa

### Por que não extrair um serviço

Os critérios usuais para extração foram checados um a um contra a situação real:

| Critério | Situação real |
|---|---|
| Escala independente entre partes | Não existe — 2.009 linhas de produção, dataset de 1.000 sessões, dois jogadores de teste, SQLite em arquivo. |
| Times independentes | Não existe — dois autores, um repositório, uma branch por tarefa (ADR 0002). |
| Ciclo de release independente | Não existe — tudo versionado e mergeado junto. |
| Fronteira tecnológica | Não existe — tudo Python 3.13, um único `poetry install`. |
| Isolamento de falha | **Já existe sem rede** — os três processos já são independentes, acoplados apenas por fila e banco. |

Extrair um serviço de inferência custaria protocolo de rede, serialização, versionamento de contrato, um segundo deploy, latência por requisição e tratamento de indisponibilidade — em troca de um isolamento que o projeto já tem de graça, já que `ml/` é importado como biblioteca por um único processo.

Mais importante: extrair antes de corrigir o acoplamento **congelaria o problema**. A dependência `ml/ → api/schemas` atravessaria a fronteira de rede, e os dois lados precisariam concordar sobre `BartlePersona` sem que existisse um lugar comum onde ela estivesse definida. Um import ruim viraria um contrato distribuído ruim.

### Por que uma camada de vocabulário, e não `shared/` ou `common/`

Um pacote chamado `shared/` ou `common/` atrai qualquer coisa que não tenha lugar óbvio e vira depósito em poucas semanas. `domain/` tem critério de entrada enunciável em uma frase — vocabulário do domínio, sem dependências — e esse critério é verificado por teste automatizado, não pela disciplina de quem revisa.

### Por que agora, e não como dívida registrada

A alternativa considerada era registrar o acoplamento como dívida assumida e seguir. Foi rejeitada por duas razões: a correção é composta de movimentações de declaração, com 208 testes já existentes como rede — o mesmo padrão de refatoração seguro usado na extração do núcleo de `ml/`; e o acoplamento `worker → simulator` é bloqueante para um item já previsto na evolução do projeto, não para um futuro hipotético.

## Consequências

### Positivas

* `ml/` passa a carregar sem FastAPI nem Pydantic (verificado: `sys.modules` após importar `ml.persona_model` não contém nenhum dos dois), o que o torna utilizável em análise, batch scoring ou um segundo consumidor.
* O worker deixa de depender do simulador, destravando a integração com fontes externas de eventos prevista no `CLAUDE.md`.
* Worker e migrações Alembic deixam de exigir o pacote da API.
* A Taxonomia de Bartle passa a ter fonte única, eliminando a divergência silenciosa entre `simulator/` e `api/`.
* O grafo de dependências internas passa a ter direção única: `api/`, `ml/`, `simulator/` e `worker/` dependem de `domain/` e `persistence/`, e nunca uns dos outros em sentido invertido.
* Adicionar um terceiro modelo de ML ou um segundo consumidor de eventos deixa de exigir decisão sobre onde declarar vocabulário.

### Negativas / Limites

* Mais um nível de indireção: quem lê `ml/persona_model.py` precisa de um salto a mais para achar a definição de `BartlePersona`. É o custo de ter fonte única.
* Dois pacotes novos com pouquíssimo código dentro. Em um projeto deste tamanho isso pode parecer cerimônia; a justificativa é o grafo de dependências, não o volume.
* `domain/` pode virar depósito com o tempo. Mitigado pelo teste de AST, mas o teste só proíbe imports — não impede alguém de declarar ali algo que não é vocabulário.
* A ordem de `BartlePersona` está congelada por causa do dataset semeado. É um acoplamento real entre uma declaração de domínio e um arquivo de dados, documentado no próprio Enum e coberto por teste, mas é um acoplamento.
* A decisão de não extrair serviço vale para o tamanho atual. Ela deve ser reavaliada se aparecer escala, time ou ciclo de release independentes — e a camada de domínio, criada agora, é precisamente o que tornaria essa extração viável no futuro.

## Referências

* ADR 0004 — banco de dados e primeira tabela (origem de `api/database.py`).
* ADR 0006 — migrações com Alembic (consumidora de `persistence/`).
* ADR 0008 — worker subscriber e tabela `player_features`.
* ADR 0010 — classificador KNN e endpoint de persona (origem de `BartlePersona` em `api/schemas.py`).
* `docs/aula6/etapa4-revisao-arquitetural.md` — levantamento que motivou esta ADR.
* `openspec/changes/extract-domain-layer/` — proposal, design e tasks da implementação.
