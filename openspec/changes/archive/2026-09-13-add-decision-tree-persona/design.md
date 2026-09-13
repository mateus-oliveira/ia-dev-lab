## Context

`ml/knn.py` foi escrito (ADR 0010) como o único módulo de ML do projeto e, por isso, acumulou três
responsabilidades que só agora se separam:

1. **contrato de dados** — `DATASET_PATH`, `FEATURE_COLUMNS`, `LABEL_COLUMN`;
2. **pipeline** — `load_dataset`, `LabelEncoder`, `StandardScaler`, `train_test_split`, acurácia e
   `classification_report`, validação estrita das features na predição;
3. **estimador** — `KNeighborsClassifier(n_neighbors=5)`.

Apenas (3) é específico do KNN. (1) e (2) valem para qualquer classificador tabular treinado sobre
`sessions_features.csv`. O consumo desses artefatos já é indireto: `api/app.py` chama
`train_classifier()` no `lifespan` e `api/routes/players.py` importa `FEATURE_COLUMNS`,
`PersonaClassifier` e `predict_persona`.

## Goals / Non-Goals

**Goals:**
- Adicionar um segundo modelo sem duplicar carga de dataset, encoding, escalonamento, divisão
  treino/teste nem cálculo de métricas.
- Manter a interface pública de cada módulo de modelo simétrica, de modo que um terceiro modelo
  seja um arquivo novo e nada mais.
- Expor as duas predições no endpoint em um contrato em que cada persona seja atribuível ao modelo
  que a produziu.

**Non-Goals:**
- Não é objetivo decidir qual modelo é "o melhor" nem escolher um vencedor em runtime: a resposta
  entrega as duas predições e a interpretação fica com quem consome.
- Não é objetivo introduzir ensemble, votação, pesos ou desempate entre os modelos.
- Não é objetivo extrair importância de features da árvore (explicabilidade está fora do escopo
  atual do `CLAUDE.md`), ainda que a estrutura escolhida deixe isso a um passo de distância.
- Não é objetivo tornar o conjunto de modelos configurável em runtime (por variável de ambiente ou
  parâmetro de requisição): os modelos disponíveis são decididos em tempo de código.

## Decisions

### Núcleo compartilhado parametrizado pelo estimador, não por herança

`ml/persona_model.py` expõe `train_persona_classifier(estimator, ...)` e
`evaluate_persona_classifier(estimator_factory, ...)`, recebendo o estimador scikit-learn já
construído (ou uma fábrica, no caso da avaliação, que precisa de uma instância limpa por execução).
Cada módulo de modelo fornece um `build_estimator()` e duas camadas finas que repassam ao núcleo.

Alternativas consideradas:

- *Classe base abstrata `BasePersonaClassifier` com subclasses `KnnPersonaClassifier` e
  `DecisionTreePersonaClassifier`*: é a forma "clássica", mas aqui a variação entre modelos é um
  único objeto (o estimador), não comportamento. Herança adicionaria uma hierarquia inteira para
  parametrizar um argumento, e o scikit-learn já fornece a abstração comum (`fit`/`predict`).
  Rejeitada por excesso de cerimônia.
- *Um único módulo com `if model == "knn": ... else: ...`*: concentra a escolha em um lugar, mas
  transforma cada novo modelo em uma edição de código existente em vez de um arquivo novo, e é
  justamente o acoplamento que a extração busca eliminar. Rejeitada.
- *Passar a classe do estimador e os hiperparâmetros separadamente*: obrigaria o núcleo a conhecer
  a assinatura de cada estimador. Rejeitada — passar o objeto pronto mantém o núcleo ignorante
  quanto ao algoritmo.

### `StandardScaler` é mantido no núcleo, inclusive para a árvore

Árvores de decisão são invariantes a transformações monotônicas por feature: escalonar não muda um
único split, e portanto não muda a predição. Manter o `StandardScaler` no caminho da árvore é,
tecnicamente, trabalho inútil.

Ainda assim, ele fica: o custo é desprezível (uma multiplicação por linha em um dataset de 1000
linhas) e a alternativa — um pipeline condicional por modelo — reintroduziria no núcleo exatamente
o conhecimento sobre o algoritmo que a extração remove, além de criar dois caminhos de dados para
testar em vez de um. Uniformidade do pipeline vence micro-otimização. Registrado aqui para que a
escolha seja legível como decisão, e não como descuido.

### Hiperparâmetros da árvore: `max_depth=6`, `random_state` fixo

`max_depth` limitado evita que a árvore memorize o dataset sintético (que tem separação bastante
nítida entre personas) e produza acurácia irrealisticamente alta; `random_state` fixo mantém a
reprodutibilidade que o projeto já adota em `DEFAULT_RANDOM_STATE`. O valor 6 é um ponto de partida
razoável para 8 features e 4 classes, não um ótimo — não houve busca de hiperparâmetros, e isso é
uma limitação consciente desta change.

### Chave do modelo é o contrato

Cada modelo tem uma chave estável (`knn`, `decision_tree`) que aparece em três lugares: o
dicionário `app.state.persona_classifiers`, o campo correspondente de `PersonaResponse` e a opção
`--model` de `evaluate_model.py`. A chave é definida no módulo do próprio modelo (`MODEL_KEY`),
para que o nome não seja redigitado em cada camada.

### Formato da resposta: um campo por modelo, no nível raiz

Decidido pelo desenvolvedor no checkpoint humano (ver `docs/aula6/etapa3-checkpoint.md`):

```json
{"player_id": "player_0001", "knn": "Killer", "decision_tree": "Explorer"}
```

O agente havia proposto aninhar as predições sob uma chave `predictions`; o desenvolvedor editou a
proposta para a forma plana, mais simples de consumir e de ler na documentação interativa do
FastAPI. O trade-off aceito é que adicionar um terceiro modelo passa a exigir um campo novo no
schema (e não apenas uma chave nova em um dicionário) — o que é aceitável porque o conjunto de
modelos é decidido em tempo de código, não em runtime.

`persona` é **removido**, não mantido como alias do KNN: preservá-lo faria o KNN parecer "o modelo
principal" por acidente histórico, exatamente a assimetria que a change quer eliminar. O projeto já
tem precedente de quebra deliberada de contrato neste endpoint (a change `knn-persona-classifier`
removeu o `player_id` do path).

### Uma leitura de features, duas predições

A linha mais recente de `player_features` é lida **uma vez** por requisição e submetida aos dois
modelos. Ler duas vezes abriria a possibilidade de os modelos responderem sobre estados diferentes
do banco, caso o worker inserisse uma linha nova entre as duas leituras — uma inconsistência real,
já que o worker escreve continuamente.

## Risks / Trade-offs

- **Quebra de contrato**: qualquer cliente que leia `response["persona"]` para de funcionar. Aceito
  e explicitado; a POC não tem cliente externo e o endpoint é consumido manualmente.
- **Startup mais lento**: dois treinos em vez de um. Irrelevante nesta escala (1000 linhas), mas
  cresce linearmente com o número de modelos e eventualmente justificaria persistir artefatos.
- **Divergência entre modelos sem critério de desempate**: a resposta pode trazer duas personas
  diferentes para o mesmo jogador, sem indicar qual seguir. É o comportamento desejado nesta change
  (a divergência é o dado de interesse), mas é uma decisão que um consumidor real precisaria
  resolver.
- **Regressão silenciosa no KNN durante o refactor**: a extração mexe no caminho de código que hoje
  serve a API. Mitigado pelo ciclo TDD: os testes existentes de `test_knn.py` e `test_persona.py`
  permanecem verdes durante toda a refatoração, e são a rede que autoriza mexer.

## Migration Plan

Sem migração de dados ou de schema. A mudança de contrato vale a partir do merge; a documentação
interativa do FastAPI (`/docs`) reflete o novo formato automaticamente.

## Open Questions

- O `max_depth=6` é um chute informado, não resultado de busca de hiperparâmetros. Se a árvore
  ficar sistematicamente abaixo do KNN, vale uma change futura com validação cruzada.
