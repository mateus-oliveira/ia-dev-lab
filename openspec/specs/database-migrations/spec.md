# database-migrations Specification

## Purpose

Garantir que o schema do banco de dados SQLite do projeto seja evoluído de forma versionada e reprodutível, com histórico de alterações e capacidade de reverter uma migração, em vez de ser criado por lógica ad-hoc embutida no código da API.

## Requirements

### Requirement: Schema aplicado por migrações versionadas
O sistema SHALL definir o schema do banco de dados SQLite exclusivamente por meio de migrações versionadas, aplicadas por um comando explícito. A inicialização da aplicação (API) NÃO SHALL criar ou alterar tabelas automaticamente.

#### Scenario: Aplicar migrações em um banco novo
- **WHEN** um desenvolvedor roda o comando de aplicação de migrações em um ambiente sem banco de dados existente
- **THEN** o arquivo de banco de dados é criado com todas as tabelas até a revisão mais recente, incluindo a tabela `users` definida na ADR 0004

#### Scenario: Iniciar a API sem aplicar migrações
- **WHEN** a API é iniciada em um ambiente cujo banco de dados ainda não teve nenhuma migração aplicada
- **THEN** a aplicação sobe normalmente (sem criar tabelas), e qualquer operação que dependa das tabelas ausentes falha de forma explícita, evidenciando que o schema não foi provisionado

### Requirement: Histórico de revisões do schema
Toda alteração de schema (criação, modificação ou remoção de tabela/coluna) SHALL ser registrada como uma nova revisão de migração, identificável e ordenada em relação às revisões anteriores.

#### Scenario: Consultar a revisão atual do banco
- **WHEN** um desenvolvedor consulta a revisão atual aplicada a um banco de dados
- **THEN** o sistema informa o identificador da última migração aplicada naquele banco

#### Scenario: Nova tabela adicionada ao domínio
- **WHEN** uma nova tabela de domínio (ex.: eventos, sessões, perfis Bartle) precisa ser adicionada ao schema em uma change futura
- **THEN** essa alteração é expressa como uma nova revisão de migração que parte da revisão mais recente existente, sem modificar revisões já aplicadas

### Requirement: Migração inicial equivalente ao schema atual
O sistema SHALL fornecer uma migração inicial que reproduz exatamente o schema hoje criado pela inicialização automática da API (tabela `users` da ADR 0004: `id`, `name`, `username` único, `password`), permitindo que bancos SQLite já existentes sejam marcados nessa revisão sem perda de dados.

#### Scenario: Marcar um banco já existente na revisão inicial
- **WHEN** um desenvolvedor possui um `db.sqlite3` criado pela inicialização automática anterior (com a tabela `users` já presente)
- **THEN** é possível marcar esse banco como estando na revisão inicial das migrações, sem recriar ou alterar os dados existentes na tabela `users`

### Requirement: Reversão de migração
O sistema SHALL permitir reverter a última migração aplicada, restaurando o schema à revisão anterior.

#### Scenario: Reverter a migração mais recente
- **WHEN** um desenvolvedor solicita a reversão da última migração aplicada a um banco de dados
- **THEN** o schema do banco volta ao estado da revisão imediatamente anterior, sem afetar dados de tabelas não relacionadas à migração revertida
