# player-persona-inference Specification

## Purpose

Entregar o perfil do jogador na Taxonomia de Bartle (`Killer`, `Achiever`, `Socializer`, `Explorer`) previsto por um classificador de Machine Learning treinado com o dataset sintético rotulado, aplicado às features mais recentes que a pipeline (simulador → fila → worker/ETL) persistiu para o jogador autenticado.

## Requirements

### Requirement: Consulta do perfil do jogador autenticado

A API SHALL expor uma rota GET de consulta de perfil que identifica o jogador **exclusivamente** pelo usuário autenticado no Bearer Token JWT, sem aceitar identificador de jogador como parâmetro de rota, de consulta ou de corpo. A rota SHALL permanecer protegida: requisições sem credencial válida SHALL ser rejeitadas com `401 Unauthorized` antes de qualquer acesso a dados ou inferência.

#### Scenario: Consulta autenticada retorna o perfil do próprio jogador

- **WHEN** uma requisição GET de consulta de perfil é enviada com um Bearer Token JWT válido de um jogador que possui features registradas pela pipeline
- **THEN** a API responde `200 OK` com um corpo JSON cujo `player_id` é o identificador do jogador autenticado (e não um valor fornecido pelo cliente) e cujo campo de perfil contém a persona prevista

#### Scenario: Requisição sem credencial é rejeitada

- **WHEN** uma requisição GET de consulta de perfil é enviada sem cabeçalho `Authorization`
- **THEN** a API responde `401 Unauthorized` e não consulta features nem executa inferência

#### Scenario: Credencial inválida ou expirada é rejeitada

- **WHEN** uma requisição GET de consulta de perfil é enviada com um Bearer Token JWT malformado, com assinatura inválida ou expirado
- **THEN** a API responde `401 Unauthorized` e não consulta features nem executa inferência

#### Scenario: Nenhum jogador pode consultar o perfil de outro

- **WHEN** dois jogadores distintos, cada um com features próprias registradas, consultam a rota de perfil com seus respectivos tokens
- **THEN** cada resposta reflete exclusivamente as features do jogador dono do token usado, sem que exista qualquer forma de a requisição selecionar outro jogador

### Requirement: Predição a partir das features mais recentes do jogador

A API SHALL derivar as personas retornadas das features agregadas mais recentes registradas para o jogador autenticado pela pipeline de ingestão (ADR 0008). Quando houver histórico com mais de um registro para o jogador, SHALL ser usado o registro mais recente. As features do jogador SHALL ser lidas **uma única vez por requisição** e submetidas a **todos** os modelos disponíveis, de modo que as predições retornadas descrevam necessariamente o mesmo estado dos dados. Cada predição SHALL ser produzida por um classificador de Machine Learning treinado com o dataset sintético rotulado — não por lógica mockada, aleatória ou derivada do identificador do jogador.

#### Scenario: Registro mais recente é o usado na predição

- **WHEN** o jogador autenticado possui vários registros de features no histórico e consulta a rota de perfil
- **THEN** todas as personas retornadas correspondem a predições sobre o registro mais recente do jogador, ignorando os anteriores

#### Scenario: Perfil evolui quando novas features chegam

- **WHEN** um novo registro de features com comportamento caracteristicamente distinto é adicionado para o jogador autenticado e a rota de perfil é consultada novamente
- **THEN** a resposta reflete as predições sobre o novo registro, podendo apresentar personas diferentes das da consulta anterior

#### Scenario: Todos os modelos respondem sobre o mesmo estado dos dados

- **WHEN** a rota de perfil é consultada e mais de um modelo está disponível
- **THEN** todas as predições da resposta derivam de uma mesma leitura das features do jogador, sem que um modelo possa responder sobre um registro mais novo que o outro

#### Scenario: Jogador sem features registradas

- **WHEN** o jogador autenticado não possui nenhum registro de features (a pipeline ainda não processou eventos dele) e consulta a rota de perfil
- **THEN** a API responde `404 Not Found` com mensagem indicando a ausência de features para o jogador, sem inventar ou sortear uma persona e sem executar nenhum dos modelos

### Requirement: Contrato de resposta restrito à Taxonomia de Bartle

O corpo de resposta de sucesso SHALL conter o identificador do jogador autenticado e, para **cada** modelo de classificação disponível, um campo próprio identificado pelo nome do modelo, cujo valor pertence estritamente ao conjunto `Killer`, `Achiever`, `Socializer`, `Explorer`, usando exatamente a mesma grafia dos rótulos do dataset de treino. A resposta NÃO SHALL conter um campo de persona sem atribuição de modelo: toda persona retornada SHALL ser rastreável ao classificador que a produziu.

#### Scenario: Cada persona é atribuível ao modelo que a produziu

- **WHEN** a rota de perfil responde com sucesso
- **THEN** a resposta contém um campo por modelo disponível, nomeado pela chave do modelo, e nenhum campo de persona anônimo ou agregado

#### Scenario: Perfil pertence ao conjunto fechado de personas

- **WHEN** a rota de perfil responde com sucesso para qualquer combinação de features válidas
- **THEN** o valor de cada campo de persona é exatamente um dos quatro rótulos da Taxonomia de Bartle, e um valor fora desse conjunto nunca é serializado

#### Scenario: Modelos divergentes são ambos reportados

- **WHEN** os modelos disponíveis produzem personas diferentes para a mesma linha de features
- **THEN** a resposta reporta as duas personas, cada uma em seu campo, sem escolher vencedor, sem votação e sem omitir a divergência

### Requirement: Classificador treinado uma única vez na inicialização do backend

O classificador SHALL ser treinado uma única vez durante a inicialização do backend, a partir do dataset sintético rotulado, e reutilizado em memória por todas as requisições subsequentes. Nenhuma requisição SHALL treinar o modelo nem reler o dataset de treino. O treinamento SHALL ser somente-leitura sobre os dados de origem: os arquivos do dataset sintético NÃO SHALL ser criados, alterados ou sobrescritos pela API.

#### Scenario: Treino ocorre no startup e não por requisição

- **WHEN** o backend é inicializado e em seguida atende várias requisições de consulta de perfil
- **THEN** o dataset de treino é lido e o classificador é treinado apenas uma vez, na inicialização, e as requisições usam o modelo já treinado

#### Scenario: Dados de origem permanecem intactos

- **WHEN** o backend é inicializado e atende requisições de consulta de perfil
- **THEN** os arquivos do dataset sintético permanecem inalterados

### Requirement: Compatibilidade entre as features da pipeline e as features de treino

O conjunto e a ordem das features usadas na predição SHALL ser os mesmos usados no treino do classificador, excluindo colunas de identificação (jogador e sessão) e o rótulo de treino. Uma divergência entre as features registradas pela pipeline e as features esperadas pelo classificador SHALL resultar em falha explícita, não em predição silenciosamente incorreta.

#### Scenario: Features da pipeline alimentam o classificador sem transformação manual de nomes

- **WHEN** um registro de features produzido pela pipeline de ingestão é submetido ao classificador
- **THEN** todas as features numéricas do registro (exceto identificadores e metadados de persistência) são usadas na predição, na mesma ordem do treino

#### Scenario: Feature ausente ou desconhecida falha explicitamente

- **WHEN** é solicitada uma predição para um conjunto de features que não corresponde ao conjunto esperado pelo classificador (feature faltando ou não reconhecida)
- **THEN** a operação falha com erro explícito em vez de produzir uma persona a partir de dados incompletos

### Requirement: Modelos treinados uma única vez na inicialização

Todos os classificadores servidos pela API SHALL ser treinados uma única vez na inicialização do processo, a partir do dataset sintético rotulado, e mantidos em memória para uso por todas as requisições. Nenhuma requisição SHALL disparar treino. Uma falha de treino de qualquer modelo (dataset ausente, inválido ou incompatível) SHALL impedir a subida do servidor, em vez de degradar requisição por requisição.

#### Scenario: Nenhuma requisição retreina modelo

- **WHEN** duas requisições consecutivas são atendidas pela rota de perfil
- **THEN** ambas usam os mesmos artefatos treinados na inicialização, sem novo treino entre elas

#### Scenario: Dataset inválido impede a subida do servidor

- **WHEN** o dataset de treino está ausente ou não contém as colunas esperadas na inicialização da aplicação
- **THEN** a inicialização falha com erro explícito e a aplicação não passa a atender requisições
