## Purpose

Entregar o perfil do jogador na Taxonomia de Bartle (`Killer`, `Achiever`, `Socializer`, `Explorer`) previsto por um classificador de Machine Learning treinado com o dataset sintético rotulado, aplicado às features mais recentes que a pipeline (simulador → fila → worker/ETL) persistiu para o jogador autenticado.

## ADDED Requirements

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

A API SHALL derivar a persona retornada das features agregadas mais recentes registradas para o jogador autenticado pela pipeline de ingestão (ADR 0008). Quando houver histórico com mais de um registro para o jogador, SHALL ser usado o registro mais recente. A predição SHALL ser produzida por um classificador de Machine Learning treinado com o dataset sintético rotulado — não por lógica mockada, aleatória ou derivada do identificador do jogador.

#### Scenario: Registro mais recente é o usado na predição

- **WHEN** o jogador autenticado possui vários registros de features no histórico e consulta a rota de perfil
- **THEN** a persona retornada corresponde à predição sobre o registro mais recente do jogador, ignorando os anteriores

#### Scenario: Perfil evolui quando novas features chegam

- **WHEN** um novo registro de features com comportamento caracteristicamente distinto é adicionado para o jogador autenticado e a rota de perfil é consultada novamente
- **THEN** a resposta reflete a predição sobre o novo registro, podendo apresentar uma persona diferente da consulta anterior

#### Scenario: Jogador sem features registradas

- **WHEN** o jogador autenticado não possui nenhum registro de features (a pipeline ainda não processou eventos dele) e consulta a rota de perfil
- **THEN** a API responde `404 Not Found` com mensagem indicando a ausência de features para o jogador, sem inventar ou sortear uma persona

### Requirement: Contrato de resposta restrito à Taxonomia de Bartle

O corpo de resposta de sucesso SHALL conter o identificador do jogador autenticado e um campo de perfil cujo valor pertence estritamente ao conjunto `Killer`, `Achiever`, `Socializer`, `Explorer`, usando exatamente a mesma grafia dos rótulos do dataset de treino.

#### Scenario: Perfil pertence ao conjunto fechado de personas

- **WHEN** a rota de perfil responde com sucesso para qualquer combinação de features válidas
- **THEN** o valor do campo de perfil é exatamente um dos quatro rótulos da Taxonomia de Bartle, e um valor fora desse conjunto nunca é serializado

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
