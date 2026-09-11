## Purpose

Disponibilizar o endpoint protegido de consulta de perfil de jogador na Taxonomia de Bartle (GET /players/{player_id}/persona) utilizando resposta mockada para validação imediata do contrato da API.

## ADDED Requirements

### Requirement: Consulta Protegida de Persona do Jogador

A API DEVE (MUST) fornecer o endpoint `GET /players/{player_id}/persona` protegido obrigatoriamente por autenticação via Bearer Token JWT (`Depends(get_current_user)`), validando o parâmetro de rota `player_id` conforme a convenção de identificadores de jogadores (`^player_\d{4,}$`).

#### Scenario: Acesso bem-sucedido com token válido e ID regular
- **WHEN** uma requisição GET for enviada para `/players/player_0000/persona` acompanhada de um Bearer Token JWT válido no cabeçalho Authorization
- **THEN** a API deve responder com status HTTP 200 OK e um corpo de resposta JSON contendo o `player_id` consultado e o perfil `persona` associado.

#### Scenario: Bloqueio para requisição sem autenticação ou com token inválido
- **WHEN** uma requisição GET for enviada para `/players/player_0000/persona` sem cabeçalho Authorization ou com token JWT inválido/expirado
- **THEN** a API deve rejeitar a requisição imediatamente retornando status HTTP 401 Unauthorized.

#### Scenario: Rejeição de identificador de jogador fora do padrão
- **WHEN** uma requisição GET autenticada for enviada para `/players/{player_id}/persona` contendo um `player_id` que não obedece ao padrão `^player_\d{4,}$` (ex: `admin`, `player_12`, `player_abc`)
- **THEN** a API deve recusar o processamento e retornar status HTTP 422 Unprocessable Entity detalhando o erro de validação.

### Requirement: Contrato de Dados com Resposta Mockada

A API DEVE (MUST) responder com um schema Pydantic `PersonaResponse` cujo campo `persona` seja estritamente restrito aos quatro arquétipos da Taxonomia de Bartle (`Killer`, `Achiever`, `Socializer`, `Explorer`), gerando a resposta a partir de lógica leve mockada/stub sem carregar modelos de ML ou acessar arquivos de dados.

#### Scenario: Retorno de perfil válido segundo o Enum de Bartle
- **WHEN** o endpoint `/players/{player_id}/persona` processar uma requisição válida
- **THEN** a propriedade `persona` da resposta JSON deve pertencer exclusivamente a um dos quatro valores permitidos: "Killer", "Achiever", "Socializer" ou "Explorer".

#### Scenario: Execução isolada sem dependências pesadas
- **WHEN** o endpoint `/players/{player_id}/persona` for executado
- **THEN** a resposta deve ser gerada diretamente em memória pelo stub/mock, garantindo que nenhum arquivo de `src/data/` seja acessado e nenhuma biblioteca de treinamento/inferência de Machine Learning seja invocada.
