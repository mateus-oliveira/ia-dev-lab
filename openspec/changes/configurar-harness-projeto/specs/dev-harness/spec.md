## Purpose

Definir os controles de desenvolvimento (hooks locais, CI e proteção de branches) que garantem que contribuições humanas e de IA sigam os padrões da ADR 0002 antes de chegarem a `dev`/`main`, sem substituir a decisão final do desenvolvedor.

## ADDED Requirements

### Requirement: Verificação de qualidade antes do commit
O harness SHALL executar formatação, lint, verificação de tipos e testes rápidos automaticamente antes de cada commit local, e SHALL abortar o commit quando qualquer uma dessas verificações falhar. O hook SHALL apenas validar; ele NUNCA DEVE criar, corrigir automaticamente e commitar, ou finalizar um commit em nome do desenvolvedor.

#### Scenario: Commit com código formatado corretamente e testes passando
- **WHEN** o desenvolvedor executa `git commit` com arquivos Python formatados, sem erros de lint/tipo e com os testes rápidos passando
- **THEN** o hook de pré-commit conclui com sucesso e o commit é criado normalmente

#### Scenario: Commit com falha de lint, formatação ou testes
- **WHEN** o desenvolvedor executa `git commit` e a formatação, o lint, a verificação de tipos ou os testes rápidos falham
- **THEN** o hook de pré-commit bloqueia o commit e reporta qual verificação falhou, sem alterar arquivos automaticamente nem criar o commit

### Requirement: Validação da mensagem de commit
O harness SHALL validar que toda mensagem de commit segue o padrão `<PREFIXO>: <descrição>` definido na ADR 0002, com `<PREFIXO>` sendo um de `ADD`, `UPDATE`, `FIX`, `REMOVE`, `REFACTOR`, `DOCS`, `TEST`. O harness SHALL rejeitar commits cuja mensagem não corresponda a esse padrão.

#### Scenario: Mensagem de commit no padrão esperado
- **WHEN** o desenvolvedor cria um commit com mensagem iniciando por um prefixo válido seguido de `: ` e uma descrição (ex.: `ADD: script de validação de branch`)
- **THEN** o commit é aceito

#### Scenario: Mensagem de commit fora do padrão
- **WHEN** o desenvolvedor cria um commit com mensagem sem um prefixo válido (ex.: `ajustes` ou `Fix bug`)
- **THEN** o commit é rejeitado e o motivo (prefixo ausente ou inválido) é reportado ao desenvolvedor

### Requirement: Validação da branch atual
O harness SHALL fornecer um comando que verifica se a branch atual é compatível com o tipo de alteração sendo feita, e SHALL alertar ou bloquear operações de commit/push quando a branch atual for `main` ou `dev` diretamente, reforçando o fluxo `feature/* → dev → main` da ADR 0002.

#### Scenario: Alteração em branch de tarefa válida
- **WHEN** o desenvolvedor está em uma branch no formato `<tipo>/<descricao-curta>` (ex.: `feature/pipeline-ingestao`) e executa a verificação de branch
- **THEN** a verificação é concluída com sucesso, sem bloqueio

#### Scenario: Tentativa de commit direto em main ou dev
- **WHEN** o desenvolvedor está com a branch `main` ou `dev` selecionada e tenta commitar ou fazer push diretamente
- **THEN** o harness bloqueia ou alerta claramente que essa operação não é permitida nessas branches, referenciando o fluxo da ADR 0002

### Requirement: Detecção de arquivos sensíveis
O harness SHALL impedir o commit de segredos, credenciais, arquivos de ambiente (`.env`), ambientes virtuais, artefatos de execução e dados pessoais/identificáveis de jogadores. Eventos e dados usados no projeto DEVEM permanecer sintéticos.

#### Scenario: Commit sem arquivos sensíveis
- **WHEN** o conjunto de arquivos staged para commit não contém segredos, `.env`, diretórios de ambiente virtual nem dados pessoais
- **THEN** a verificação de arquivos sensíveis passa e o commit prossegue para as demais validações

#### Scenario: Tentativa de commit de um arquivo sensível
- **WHEN** o conjunto de arquivos staged inclui um arquivo de segredo/credencial, um `.env`, um diretório de ambiente virtual, ou um arquivo com dados pessoais/identificáveis de jogadores
- **THEN** o harness bloqueia o commit e informa quais arquivos foram identificados como sensíveis

### Requirement: Relatório de alterações fora do escopo
O harness SHALL fornecer um comando que, antes de uma tarefa ser considerada concluída, lista os arquivos modificados e a diferença em relação à branch de origem, permitindo identificar alterações acidentais em dados brutos (`data/events.csv`, `data/sessions_features.csv`), configurações ou outros módulos fora do escopo da tarefa.

#### Scenario: Alterações restritas ao escopo da tarefa
- **WHEN** o desenvolvedor executa o comando de relatório de escopo ao final de uma tarefa cujas alterações tocam apenas os arquivos esperados
- **THEN** o relatório lista esses arquivos e não sinaliza nenhum alerta de escopo

#### Scenario: Alteração acidental em dado bruto ou fora do escopo
- **WHEN** o relatório de escopo é executado e o diff em relação à branch de origem inclui `data/events.csv`, `data/sessions_features.csv` ou outro arquivo não relacionado à tarefa declarada
- **THEN** o relatório sinaliza esse(s) arquivo(s) como potencialmente fora de escopo para revisão do desenvolvedor

### Requirement: CI executa a suíte de testes em Pull Requests para dev
O harness SHALL executar, em cada Pull Request direcionado à branch `dev`, um workflow de CI que roda a suíte de testes unitários (pytest) em um ambiente limpo, independente de hooks locais estarem instalados. O merge de um Pull Request para `dev` NUNCA DEVE ser considerado apto enquanto os testes estiverem falhando.

#### Scenario: Pull Request para dev com todos os testes passando
- **WHEN** um Pull Request destinado a `dev` é aberto ou atualizado e todos os testes unitários passam
- **THEN** o Pull Request é marcado como apto para merge do ponto de vista de CI

#### Scenario: Pull Request para dev com testes falhando
- **WHEN** um Pull Request destinado a `dev` é aberto ou atualizado e algum teste unitário falha
- **THEN** o Pull Request é marcado como não apto para merge do ponto de vista de CI

### Requirement: Bloqueio técnico de commits automáticos por agentes de IA
O harness SHALL bloquear, de forma técnica e incondicional, qualquer comando `git commit`, `git push` ou `git merge` disparado por um agente de IA através das ferramentas de execução do Claude Code — mesmo quando o desenvolvedor solicitar essa operação na conversa. Commits, pushes e merges DEVEM ser sempre executados manualmente pelo desenvolvedor, após validação, fora da automação do agente.

#### Scenario: Agente de IA tenta executar git commit, git push ou git merge
- **WHEN** um agente de IA tenta executar `git commit`, `git push` ou `git merge` como parte de uma tarefa
- **THEN** o harness bloqueia a execução do comando e informa que essa operação deve ser realizada manualmente pelo desenvolvedor

#### Scenario: Desenvolvedor solicita explicitamente que o agente commite
- **WHEN** o desenvolvedor pede ao agente de IA, na conversa, para executar `git commit`, `git push` ou `git merge`
- **THEN** o harness ainda assim bloqueia a execução do comando pelo agente, sem exceção

#### Scenario: Desenvolvedor executa o commit manualmente
- **WHEN** o desenvolvedor, fora da automação do agente, executa `git commit`, `git push` ou `git merge` diretamente
- **THEN** a operação ocorre normalmente, sujeita apenas aos demais controles do harness (mensagem de commit, branch atual, arquivos sensíveis)

### Requirement: Reprodutibilidade das dependências de desenvolvimento
O harness SHALL centralizar e fixar as versões das ferramentas de formatação, lint, verificação de tipos, testes e pre-commit em um arquivo de dependências versionado, de modo que a execução local e a execução em CI utilizem as mesmas versões.

#### Scenario: Instalação local e execução de CI usam as mesmas versões
- **WHEN** o ambiente local e o ambiente de CI instalam as dependências de desenvolvimento a partir do arquivo de dependências versionado
- **THEN** ambos utilizam as mesmas versões das ferramentas de lint, formatação, tipos, testes e pre-commit
