## Context

Ver `proposal.md` — "Why" para a motivação. O estado atual relevante para o desenho:

- `src/player_modeling/ml/knn.py` existe como script exploratório (portado de notebook): executa tudo em nível de módulo, com `PATH` placeholder, `print`s e `exit()` em caso de erro. Nada dele é importável sem disparar treino e I/O.
- `src/player_modeling/api/routes/players.py` expõe `GET /players/{player_id}/persona` com stub determinístico (`resolve_mock_persona`), protegido por `Depends(get_current_user)` (ADR 0005), que devolve `{"id", "name", "username"}` do usuário autenticado.
- `player_id` e `username` são o mesmo identificador: o publisher (ADR 0007) publica eventos para os `PLAYER_USERNAME_1`/`PLAYER_USERNAME_2` registrados via `POST /auth/register`, e ambos respeitam o padrão `^player_\d{4,}$` validado em `UserRegisterRequest`.
- A tabela `player_features` (migração `0473827a6cf7`, ADR 0008) guarda **histórico**: uma linha por mensagem consumida da fila, com índice composto `(player_id, id)` criado justamente para a consulta da linha mais recente de um jogador.
- As colunas de feature persistidas por `worker/repository.py` (derivadas de `worker/features.py`) são exatamente as colunas de treino de `src/data/sessions_features.csv`, exceto `session_id`, `player_id` e o rótulo `true_persona`: `n_events`, `pct_attack`, `pct_explore`, `pct_social`, `pct_quest_complete`, `pct_retry`, `avg_decision_time_ms`, `fail_rate`.
- `mypy` roda com `disallow_untyped_defs = true` para `player_modeling.*` e `ignore_missing_imports = true` global — relevante porque `sklearn` não publica stubs de tipos.

## Goals / Non-Goals

**Goals:**

- Separar claramente três responsabilidades: treino do classificador (domínio `ml/`), cache do modelo treinado (ciclo de vida da aplicação, `api/app.py`) e consulta/inferência por requisição (rota em `api/routes/players.py`).
- Manter `ml/knn.py` puro e testável: funções sem estado global, sem `print`, sem leitura de `cwd`, sem efeito colateral no import.
- Garantir alinhamento estrutural entre as features persistidas pela pipeline e as features de treino, com falha explícita em caso de divergência.
- Preservar as decisões de modelagem que o desenvolvedor já validou no notebook (KNN com `k=5`, `StandardScaler`, `LabelEncoder`).

**Non-Goals:**

- Otimizar hiperparâmetros, comparar algoritmos ou medir/reportar métricas em produção (a avaliação fica disponível para uso em teste/análise, não no caminho da requisição).
- Serializar o modelo em disco ou introduzir um registry de modelos.
- Reprocessar histórico: a inferência usa somente a linha mais recente, sem janela/agregação temporal.

## Decisions

### 1. Treinar no startup da API, em memória, em vez de versionar um modelo serializado

- **Decisão:** o `lifespan` do FastAPI treina o classificador uma vez na subida (`make run`) e guarda os artefatos em `app.state`; o modelo vive apenas em memória, pelo tempo de vida do processo.
- **Racional:** o dataset é pequeno (1000 sessões, 8 features) e o treino de um KNN sobre ele é praticamente instantâneo, então o custo no startup é irrelevante. Em troca, elimina-se o problema de um artefato binário desatualizado versus o CSV versionado: o modelo é sempre coerente com o dataset presente no repositório, e regenerar o dataset (`generate_raw_events.py`) basta para o próximo startup refletir os novos dados. Também evita adicionar `joblib`/`pickle` e a discussão de onde guardar e como versionar o `.pkl` — decisão que faria sentido apenas com custo de treino relevante ou necessidade de reprodutibilidade auditável, o que não é o caso nesta POC.
- **Alternativas consideradas:**
  - *Treinar offline e carregar um `.pkl` no startup*: descartado por adicionar um artefato binário versionado (ou um passo manual de build) sem ganho perceptível de tempo de subida neste tamanho de dataset; fica como evolução natural quando o treino passar a ser caro.
  - *Treinar sob demanda na primeira requisição (lazy) com cache*: descartado por deslocar a latência e as falhas de carga de dados para uma requisição de usuário, e por exigir controle de concorrência. Falhar no startup é preferível: um dataset ausente ou corrompido derruba a subida do servidor de forma visível, em vez de produzir `500` intermitente.
  - *Treinar por requisição*: descartado (desperdício óbvio e latência proporcional ao dataset).

### 2. `ml/knn.py` como funções puras devolvendo um artefato imutável; cache em `app.state`

- **Decisão:** `ml/knn.py` expõe (a) uma função de treino que lê o CSV e devolve uma dataclass imutável (`frozen`) com `KNeighborsClassifier`, `StandardScaler`, `LabelEncoder` e a tupla ordenada de colunas de feature, e (b) uma função de predição que recebe esse artefato mais um dicionário de features e devolve `BartlePersona`. Nenhum singleton, cache ou estado global mora em `ml/`.
- **Racional:** mantém o domínio de ML independente do framework web e trivialmente testável (treinar num teste é uma chamada de função, sem subir aplicação). O ciclo de vida do modelo é uma preocupação da aplicação, então pertence a `api/app.py`/`app.state` — que é também o mecanismo que o FastAPI oferece para estado de processo compartilhado entre requisições.
- **Alternativas consideradas:**
  - *`@functools.lru_cache` ou variável de módulo em `ml/knn.py`*: mais curto, mas esconde estado global no domínio, atrapalha testes (cache compartilhado entre casos) e torna o import não determinístico quanto a I/O.
  - *Classe `PersonaClassifier` com método `fit`/`predict` própria*: descartada por ser uma camada extra sobre a API do scikit-learn sem ganho — a dataclass já agrupa o necessário, e a função de predição documenta explicitamente o contrato de entrada (dicionário de features da pipeline).

### 3. Treinar para servir com o dataset completo; avaliação como função separada

- **Decisão:** a função usada pelo startup treina com **todas** as linhas do dataset. O `train_test_split` + acurácia + `classification_report` do script original vira uma função de avaliação separada, usada por testes/análise, e não é executada na subida da API.
- **Racional:** reter 30% dos dados fora do treino do modelo que serve produção reduz qualidade sem benefício — a avaliação serve para decidir se o modelo é bom, não para servi-lo. Separar as duas responsabilidades também evita `print`s e custo de avaliação no startup, mantendo a capacidade de verificar a qualidade do classificador em teste.
- **Trade-off:** o modelo em execução não tem métrica reportada no log de startup. Aceitável nesta POC: a métrica é verificável por teste e pela função de avaliação, e a change não promete observabilidade de ML (fora de escopo, como explicabilidade e importância de features).

### 4. Ordem de features explícita e validação estrita na predição

- **Decisão:** as colunas de feature são declaradas explicitamente (constante no módulo, na ordem do treino) em vez de derivadas por posição (`iloc[:, :-1]`); a função de predição valida que o dicionário recebido contém exatamente esse conjunto e monta o vetor nessa ordem, falhando com erro explícito caso falte ou sobre feature.
- **Racional:** `iloc[:, :-1]`/`iloc[:, -1]` depende silenciosamente da ordem das colunas do CSV — se `generate_raw_events.py` reordenar colunas ou incluir uma nova, o modelo passaria a treinar com o alvo errado sem qualquer sinal. Como o CSV de treino e a tabela `player_features` evoluem em arquivos diferentes, a lista explícita é o ponto único que mantém treino e inferência acoplados de forma verificável (requisito "Compatibilidade entre as features da pipeline e as features de treino" em `specs/player-persona-inference/spec.md`).
- **Alternativa considerada:** confiar na ordem do CSV e na ordem do `SELECT` — descartado pelo risco de erro silencioso descrito acima.

### 5. Rota `GET /players/me/persona`

- **Decisão:** substituir `GET /players/{player_id}/persona` por `GET /players/me/persona`, mantendo o prefixo `/players` do router existente.
- **Racional:** o segmento `me` sinaliza no próprio path que o recurso é "o perfil do jogador autenticado", seguindo o precedente já estabelecido no projeto por `GET /auth/me` (ADR 0005). Também deixa espaço para, no futuro, existir uma rota administrativa com `player_id` explícito sem colidir com este contrato.
- **Alternativas consideradas:**
  - *`GET /players/persona`*: mais curto, mas ambíguo sobre de quem é o perfil e sem o precedente de `/auth/me`.
  - *Manter `{player_id}` no path e apenas validar que é igual ao usuário autenticado (403 se diferente)*: descartado por pedido explícito do desenvolvedor e porque duplica informação na requisição — o path passaria a aceitar um valor que só pode ter um único conteúdo válido, exigindo um erro a mais para cobrir o caso inútil.
- **Consequência (BREAKING):** clientes do contrato anterior precisam mudar a URL; o `422` de formato de `player_id` deixa de existir (não há mais entrada do cliente a validar).

### 6. Consulta da linha mais recente e comportamento na ausência de dados

- **Decisão:** `SELECT ... FROM player_features WHERE player_id = ? ORDER BY id DESC LIMIT 1`, usando o `username` do usuário autenticado; quando não há linha, responder `404 Not Found` com mensagem explicando que a pipeline ainda não processou eventos do jogador.
- **Racional:** `id` é `INTEGER PRIMARY KEY AUTOINCREMENT` e o índice `(player_id, id)` foi criado na ADR 0008 exatamente para essa consulta, o que a torna eficiente e determinística — mais confiável que ordenar por `created_at`, que é texto ISO e poderia empatar entre duas mensagens processadas no mesmo instante. O `404` respeita a regra do projeto de tratamento explícito de erros de dados em vez de ocultar a falta de dados com uma persona arbitrária.
- **Alternativa considerada:** responder `200` com `persona: null` ou uma persona padrão — descartado por mentir sobre a existência de uma predição.
- **Onde mora a consulta:** função de leitura junto da rota de jogadores em `api/`, e não em `worker/repository.py` — aquele módulo é a escrita do ETL; a leitura é uma preocupação da API e depende da sua conexão injetada (`Depends(get_db)`).

### 7. Mapeamento do rótulo previsto para o Enum `BartlePersona`

- **Decisão:** converter a classe prevista (string do `LabelEncoder`) para o Enum `BartlePersona` já existente em `api/schemas.py`, mantendo `PersonaResponse` inalterado.
- **Racional:** os rótulos de `true_persona` no dataset (`Killer`, `Achiever`, `Socializer`, `Explorer`) têm exatamente a grafia dos valores do Enum, então a conversão é direta e falha alto (`ValueError`) se o dataset trouxer um rótulo desconhecido — melhor que serializar uma string livre e violar o contrato documentado no OpenAPI. O Enum vive em `api/schemas.py` e é a fronteira da API; `ml/` devolvê-lo mantém um único vocabulário de personas no projeto, ao custo de uma dependência de `ml/` para `api/schemas.py` (aceitável: `schemas.py` não importa nada de `ml/`, logo não há ciclo).

### 8. `pandas` e `scikit-learn` como dependências de runtime

- **Decisão:** adicionar ambas ao grupo principal do `pyproject.toml` (não em `group.dev`).
- **Racional:** a API em execução treina o modelo no startup e roda inferência por requisição, então as duas bibliotecas são necessárias em produção — colocá-las em `dev` quebraria uma instalação `--without dev`. `pandas` é usada para carregar e selecionar colunas do CSV de treino (e para montar a linha de predição com nomes de coluna, evitando avisos de *feature names* do scikit-learn); `scikit-learn` fornece `KNeighborsClassifier`, `StandardScaler`, `LabelEncoder` e `train_test_split`, já usados no notebook do desenvolvedor.
- **Alternativa considerada:** ler o CSV com o módulo `csv` da biblioteca padrão e dispensar `pandas` — reduziria uma dependência pesada, mas exigiria reimplementar seleção/conversão de colunas à mão e divergiria do código que o desenvolvedor já validou. `scikit-learn` não tem substituto razoável aqui. `pandas` fica, portanto, justificada pelo alinhamento com o notebook e pela robustez na passagem de nomes de features ao estimador.
- **Nota de tipagem:** `scikit-learn` e `pandas` não fornecem stubs completos; `ignore_missing_imports = true` (já configurado) cobre isso, e as funções públicas do módulo mantêm anotações explícitas por causa de `disallow_untyped_defs`.

### 9. ADRs

- Esta change **exige uma nova ADR (`docs/adr/0010-...`)**, seguindo o precedente de uma ADR por decisão arquitetural relevante (ADR 0007 para o publisher, ADR 0008 para o worker subscriber). A ADR deve registrar: o classificador KNN como modelo do perfil Bartle, o treino em memória no startup da API (decisão 1) e a mudança do contrato para derivar o jogador do usuário autenticado (decisão 5).
- ADRs referenciadas e não alteradas: **0004** (banco/`users`), **0005** (FastAPI + JWT, origem de `get_current_user` e do precedente `/auth/me`), **0006** (Alembic — nenhuma migração nova nesta change), **0007** (publisher/`player_id` = `username`), **0008** (`player_features`, histórico e índice `(player_id, id)`).

## Risks / Trade-offs

- **[Startup mais lento e dependente do dataset]** — o processo passa a ler `src/data/sessions_features.csv` e treinar antes de aceitar requisições; dataset ausente/corrompido impede a subida. → Mitigação: falha no startup é intencional e explícita (preferível a `500` por requisição); o CSV é versionado no repositório e regenerável por `generate_raw_events.py`.
- **[Modelo treinado com dados sintéticos e rótulos gerados pelo próprio simulador]** — a acurácia observada reflete o gerador, não jogadores reais; há risco de leitura otimista das métricas. → Mitigação: manter a natureza sintética explícita na ADR 0010 e na documentação; nenhuma promessa de qualidade de produção é feita nesta change.
- **[Divergência futura entre `extract_features` e as colunas de treino]** — se a pipeline passar a produzir outro conjunto de features, a inferência quebra. → Mitigação: lista explícita de colunas (decisão 4) com falha explícita, coberta por teste que compara as features persistidas pela pipeline com as esperadas pelo classificador.
- **[Predição sobre um único lote recente]** — 15 a 20 eventos por mensagem podem gerar oscilação de persona entre consultas consecutivas, enquanto o dataset de treino tem sessões bem maiores (dezenas de eventos). → Mitigação: aceito e desejado nesta etapa (observar a evolução do perfil ao longo do tempo era o objetivo declarado do publisher na ADR 0007); qualquer suavização/janela temporal é escopo futuro.
- **[Quebra de contrato para clientes existentes]** — a rota antiga deixa de existir. → Mitigação: a POC não tem clientes externos nem frontend; `README.md`/`CLAUDE.md` são atualizados na mesma change e a mudança é sinalizada como **BREAKING** no proposal.
- **[Dependências pesadas em um projeto até agora leve]** — `pandas` + `scikit-learn` aumentam consideravelmente o tempo de instalação e o tamanho do ambiente. → Mitigação: são as bibliotecas já usadas pelo desenvolvedor no notebook e inevitáveis para o item 3 do escopo; nenhuma outra dependência de ML é adicionada.

## Migration Plan

1. Adicionar `pandas` e `scikit-learn` ao grupo principal do `pyproject.toml` e atualizar o lock (`poetry install`).
2. Reescrever `src/player_modeling/ml/knn.py` como biblioteca (treino, avaliação e predição) e atualizar a docstring de `src/player_modeling/ml/__init__.py`.
3. Treinar no `lifespan` de `src/player_modeling/api/app.py`, guardando os artefatos em `app.state`, com dependency de acesso para as rotas.
4. Substituir a rota de persona em `src/player_modeling/api/routes/players.py` (novo path, jogador do usuário autenticado, consulta da linha mais recente de `player_features`, `404` quando não houver features) e remover o stub `resolve_mock_persona`.
5. Criar `src/tests/player_modeling/ml/test_knn.py` e reescrever `src/tests/player_modeling/api/test_persona.py`; ajustar referências ao stub em outros testes.
6. Rodar o harness completo (`pytest`, `ruff check`, `ruff format`, `mypy`) e o relatório de escopo (`scripts/report_scope_diff.py`).
7. Atualizar `README.md` e `CLAUDE.md` e criar `docs/adr/0010-*`.

**Rollback:** nenhuma migração de banco e nenhum dado alterado — reverter o commit da branch restaura o endpoint stub anterior; as dependências extras podem permanecer instaladas sem efeito.
