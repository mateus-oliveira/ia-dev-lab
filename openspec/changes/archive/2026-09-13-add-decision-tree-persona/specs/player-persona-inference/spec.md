## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Modelos treinados uma única vez na inicialização

Todos os classificadores servidos pela API SHALL ser treinados uma única vez na inicialização do processo, a partir do dataset sintético rotulado, e mantidos em memória para uso por todas as requisições. Nenhuma requisição SHALL disparar treino. Uma falha de treino de qualquer modelo (dataset ausente, inválido ou incompatível) SHALL impedir a subida do servidor, em vez de degradar requisição por requisição.

#### Scenario: Nenhuma requisição retreina modelo

- **WHEN** duas requisições consecutivas são atendidas pela rota de perfil
- **THEN** ambas usam os mesmos artefatos treinados na inicialização, sem novo treino entre elas

#### Scenario: Dataset inválido impede a subida do servidor

- **WHEN** o dataset de treino está ausente ou não contém as colunas esperadas na inicialização da aplicação
- **THEN** a inicialização falha com erro explícito e a aplicação não passa a atender requisições
