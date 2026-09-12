# ADR 0010 - Classificador KNN de personas e perfil do jogador autenticado

* **Status:** Aceito
* **Data:** 2026-09-12
* **Decisão:** Adoção de um classificador KNN (`src/player_modeling/ml/knn.py`) treinado em memória na inicialização da API, e substituição do endpoint mockado `GET /players/{player_id}/persona` por `GET /players/me/persona`, que prevê o perfil do **jogador autenticado** a partir da linha mais recente de `player_features`.

## Contexto

O item 3 do objetivo inicial (`CLAUDE.md`, `docs/escopo.md`) exige um endpoint GET que retorne o perfil do jogador previsto por um modelo de ML a partir de seus eventos mais recentes. Até esta decisão, esse endpoint existia apenas como stub: a change arquivada `inference-endpoint` estabeleceu o contrato HTTP com uma persona determinística derivada do `player_id` do path, sem consultar dados nem executar inferência (limitação registrada na [ADR 0008](0008-worker-subscriber-features.md), consequências).

As duas pontas que faltavam já existem:

* a pipeline da [ADR 0007](0007-simulador-publisher-rabbitmq.md) (publisher) e da [ADR 0008](0008-worker-subscriber-features.md) (worker subscriber) alimenta continuamente a tabela de histórico `player_features`, com um índice composto `(player_id, id)` criado justamente para localizar a linha mais recente de um jogador;
* `src/data/sessions_features.csv` fornece 1000 sessões sintéticas rotuladas com `true_persona`, com exatamente as mesmas oito features que o worker persiste.

O `player_id` da pipeline é o próprio `username` cadastrado via `POST /auth/register`: o publisher publica eventos para os jogadores de teste configurados em `PLAYER_USERNAME_1`/`PLAYER_USERNAME_2`. Como a API já tem autenticação JWT ([ADR 0005](0005-fastapi-e-jwt-auth.md)) e a dependência `get_current_user` devolve o `username` do portador do token, o identificador do jogador não precisa ser informado pelo cliente.

O modelo de classificação (KNN com `k=5`, `StandardScaler` e `LabelEncoder`) foi prototipado pelo desenvolvedor em notebook antes desta change; esta decisão preserva essas escolhas de modelagem e trata do que faltava: como treinar, onde manter o modelo e como expor a predição.

## Decisões

### 1. Treino em memória na inicialização da API, sem modelo serializado

O `lifespan` do FastAPI treina o classificador uma única vez na subida (`make run`) e o mantém em `app.state.persona_classifier`. O modelo existe apenas em memória, pelo tempo de vida do processo.

O treino sobre o dataset (1000 linhas, 8 features) leva ~50 ms, então o custo no startup é irrelevante. Em troca, elimina-se a possibilidade de um artefato binário divergir do CSV versionado: o modelo é sempre coerente com o dataset presente no repositório, e regenerar o dataset (`generate_raw_events.py`) basta para o próximo startup refletir os novos dados. Também evita adicionar `joblib`/`pickle` e decidir onde versionar um `.pkl`.

**Alternativas descartadas:**

* *Treinar offline e carregar um `.pkl` no startup*: adiciona artefato binário versionado (ou passo manual de build) sem ganho perceptível de tempo de subida nesta escala. É a evolução natural quando o treino ficar caro.
* *Treinar de forma preguiçosa na primeira requisição, com cache*: desloca latência e falhas de carga de dados para uma requisição de usuário e exige controle de concorrência. Falhar no startup é preferível — um dataset ausente ou inválido derruba a subida de forma visível, em vez de gerar `500` intermitente.
* *Treinar por requisição*: desperdício, latência proporcional ao dataset.

### 2. Treinar para servir com o dataset completo; avaliação como função separada

`train_classifier()` usa **todas** as linhas do dataset. O `train_test_split` + acurácia + relatório de classificação do protótipo virou `evaluate_classifier()`, usada por testes e análises e **não** executada no startup: reter 30% dos dados fora do treino do modelo que serve requisições reduziria qualidade sem benefício, já que a avaliação serve para decidir se o modelo é bom, não para servi-lo.

Acurácia medida com a divisão estratificada padrão (`test_size=0.3`, `random_state=42`): **0,9433** — f1-score entre 0,93 e 0,96 nas quatro personas. O teste automatizado exige no mínimo 0,85, para detectar regressão sem travar em um valor exato.

**Consequência aceita:** o modelo em execução não reporta métrica no log de startup; observabilidade de ML está fora do escopo desta etapa.

### 3. Módulo de ML como biblioteca pura; estado de aplicação fora de `ml/`

`ml/knn.py` não executa nada no import (sem `print`, sem `exit()`, sem treino em nível de módulo) e não guarda estado global: o treino devolve uma dataclass `frozen` (`PersonaClassifier`) com modelo, scaler, encoder e a ordem das colunas de feature; a predição recebe esse artefato e um dicionário de features. O cache do modelo é responsabilidade da camada de API (`app.state`), consumido pelas rotas via dependency.

Isso mantém o domínio de ML independente do framework web e testável por chamada de função, sem subir aplicação. Alternativas descartadas: `functools.lru_cache`/variável de módulo em `ml/` (esconde estado global no domínio e compartilha cache entre testes) e uma classe wrapper própria sobre a API do scikit-learn (camada extra sem ganho).

O caminho do dataset é resolvido a partir de `Path(__file__)`, não do diretório de trabalho, para que o módulo funcione igual sob `make run`, `pytest` ou import direto.

### 4. Ordem de features explícita, com validação estrita na predição

As oito colunas de feature são declaradas explicitamente em `FEATURE_COLUMNS`, na ordem do treino, em vez de derivadas por posição (`iloc[:, :-1]` / `iloc[:, -1]`, como no protótipo). A predição valida que o dicionário recebido contém exatamente esse conjunto e falha com `ValueError` explícito quando falta ou sobra feature.

A versão por posição depende silenciosamente da ordem das colunas do CSV: se `generate_raw_events.py` reordenasse colunas ou incluísse uma nova, o modelo passaria a treinar contra o alvo errado sem qualquer sinal. Como o CSV de treino e a tabela `player_features` evoluem separadamente, a lista explícita é o ponto único que mantém treino e inferência acoplados de forma verificável — coberta por um teste que compara as features de `worker.features.extract_features` com as esperadas pelo classificador.

### 5. `GET /players/me/persona`: jogador derivado do token, não do path

O endpoint deixa de aceitar `player_id`. O jogador é sempre o `username` do portador do Bearer Token, seguindo o precedente de `GET /auth/me` (ADR 0005); o segmento `me` sinaliza no próprio path que o recurso é o perfil do próprio jogador autenticado e deixa espaço para uma futura rota administrativa com `player_id` explícito.

**Alternativas descartadas:** `GET /players/persona` (ambíguo sobre de quem é o perfil, sem o precedente de `/auth/me`); manter `{player_id}` e apenas rejeitar divergência com `403` (duplica informação na requisição — o path aceitaria um valor com um único conteúdo válido, exigindo um erro a mais para cobrir o caso inútil).

**Mudança incompatível:** a rota anterior deixa de existir e a validação `422` do formato de `player_id` desaparece (não há mais entrada do cliente a validar). Um jogador também deixa de poder consultar o perfil de outro. Aceitável: a POC não tem clientes externos nem frontend.

### 6. Leitura da linha mais recente e `404` na ausência de features

A consulta é `SELECT <features> FROM player_features WHERE player_id = ? ORDER BY id DESC LIMIT 1`, aproveitando o índice `(player_id, id)` da ADR 0008. Ordena-se por `id` (autoincremental) e não por `created_at`, que é texto ISO e pode empatar entre duas mensagens processadas no mesmo instante.

Quando o jogador autenticado não tem nenhuma linha, a resposta é `404 Not Found` com mensagem explicando que a pipeline ainda não processou eventos dele — em vez de `200` com persona padrão ou nula, que mentiria sobre a existência de uma predição. A função de leitura fica na camada de API, não em `worker/repository.py`: aquele módulo é a escrita do ETL.

### 7. `pandas` e `scikit-learn` como dependências de runtime

Ambas vão para o grupo principal do `pyproject.toml`, não para `group.dev`: a API em execução treina no startup e infere por requisição, então uma instalação `--without dev` precisa delas. `pandas` carrega o CSV de treino e monta a linha de predição com nomes de coluna (evitando divergência de *feature names* no scikit-learn); `scikit-learn` fornece `KNeighborsClassifier`, `StandardScaler`, `LabelEncoder` e `train_test_split`.

Descartado ler o CSV com o módulo `csv` da biblioteca padrão para evitar `pandas`: reduziria uma dependência pesada ao custo de reimplementar seleção e conversão de colunas à mão, divergindo do código já validado pelo desenvolvedor.

## Consequências

- **Positivas**:
  - O fluxo do escopo inicial está fechado de ponta a ponta: simulador → RabbitMQ → worker → banco → modelo de ML → endpoint GET, com dados reais da pipeline.
  - Cada jogador só acessa seu próprio perfil, sem que o endpoint precise de regra de autorização adicional.
  - O modelo é sempre coerente com o dataset versionado, sem artefato binário no repositório.
  - `ml/knn.py` é testável isoladamente; treino, predição e avaliação têm responsabilidades separadas.
- **Negativas / Limitações**:
  - Quebra de contrato: clientes da rota antiga precisam ser ajustados.
  - A subida da API passa a depender do dataset de treino — ausente ou inválido, o servidor não sobe (falha intencionalmente explícita).
  - A acurácia observada reflete dados sintéticos rotulados pelo próprio simulador, não jogadores reais; não é evidência de qualidade em produção.
  - A predição usa um único lote recente (15 a 20 eventos), enquanto o treino usa sessões bem maiores; o perfil pode oscilar entre consultas consecutivas. Isso é desejado nesta etapa (observar a evolução do perfil ao longo do tempo, ADR 0007), mas qualquer suavização ou janela temporal é trabalho futuro.
  - Sem métrica de qualidade exposta em runtime, e sem análise de importância de features ou explicabilidade — fora de escopo (`CLAUDE.md`, seção "Não fazer").
