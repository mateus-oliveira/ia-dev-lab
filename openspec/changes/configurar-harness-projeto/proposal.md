## Why

Antes de iniciar a implementação da pipeline de Player Modeling em `src/`, o projeto precisa de um harness de desenvolvimento que garanta que contribuições humanas e de IA sigam padrões verificáveis (ADR 0002) e que nenhuma alteração não testada, insegura ou fora de escopo chegue a `dev`/`main`. Hoje o repositório não possui hooks, CI nem proteção de branch: nada impede push direto em `main`/`dev`, commit com segredos, ou merge com testes quebrados. `docs/escopo.md` (seção 2) já define os controles necessários; esta change os implementa.

## What Changes

- Adicionar hooks de pré-commit que executam formatação, lint, verificação de tipos (Python) e testes rápidos antes de cada commit, sem criar commits automaticamente.
- Adicionar hook de verificação de mensagem de commit que valida o padrão `<PREFIXO>: <descrição>` da ADR 0002 (`ADD`, `UPDATE`, `FIX`, `REMOVE`, `REFACTOR`, `DOCS`, `TEST`).
- Adicionar um comando/script de validação da branch atual, que alerta ou bloqueia operações em `main`/`dev` conforme o fluxo da ADR 0002.
- Adicionar verificação de arquivos sensíveis (segredos, credenciais, `.env`, ambientes virtuais, artefatos de execução, dados pessoais) antes do commit.
- Adicionar um workflow de CI (GitHub Actions), disparado em Pull Requests direcionados a `dev`, que executa a suíte de testes unitários (pytest) em ambiente limpo; nenhum merge deve ser permitido com os testes falhando.
- Adicionar um hook técnico do Claude Code (`.claude/settings.json`) que bloqueia incondicionalmente qualquer comando `git commit`, `git push` ou `git merge` disparado pelo agente de IA — commits e push permanecem sempre manuais, feitos pelo desenvolvedor após validação.
- Adicionar um script/comando que reporta, antes de concluir uma tarefa, os arquivos alterados e a diferença em relação à branch de origem, para reduzir o risco de alterações fora do escopo (ex.: `data/events.csv`, configurações).
- Centralizar e fixar as dependências de desenvolvimento (lint, formatação, tipos, testes, pre-commit) para reprodutibilidade entre execução local e CI.
- Documentar no `CLAUDE.md`/`README.md` como cada controle do harness funciona, incluindo o bloqueio técnico de commits automáticos por IA.
- Registrar em ADR as decisões de ferramentas e limites do harness (o que ele bloqueia automaticamente vs. o que apenas sinaliza para revisão humana).

Esta change não implementa nenhuma funcionalidade da pipeline de Player Modeling (simulador, worker, ML, API) — apenas os controles de desenvolvimento que a antecedem.

## Capabilities

### New Capabilities
- `dev-harness`: conjunto de controles de desenvolvimento do repositório — hooks de pré-commit (lint/format/type-check/testes), validação de mensagem de commit, validação de branch atual, checagem de arquivos sensíveis, relatório de arquivos alterados fora de escopo, CI em Pull Requests e proteção de branches remotas (`main`, `dev`).

### Modified Capabilities
_Nenhuma capability existente é modificada — o projeto ainda não possui specs de pipeline implementadas._

## Impact

- **Novos arquivos/diretórios**: configuração de pre-commit (ex.: `.pre-commit-config.yaml`), scripts de validação (mensagem de commit, branch atual, arquivos sensíveis, diff de escopo) em `scripts/`, workflow de CI em `.github/workflows/`, arquivo(s) de dependências de desenvolvimento.
- **Configuração do Claude Code**: novo hook em `.claude/settings.json` bloqueando `git commit`/`git push`/`git merge` disparados pelo agente de IA.
- **Documentação**: atualização de `CLAUDE.md`, `README.md` e um novo ADR descrevendo as ferramentas escolhidas e os limites do harness (bloqueio automático vs. alerta para revisão humana).
- **Fora de escopo** (ver seção "Não fazer" do `CLAUDE.md`): nenhuma funcionalidade de simulador, worker/ETL, banco de dados, modelo de ML ou endpoint da pipeline; nenhum frontend, autenticação/autorização, integração com PlayFab/Databricks/Redis, infraestrutura de produção ou deploy.
