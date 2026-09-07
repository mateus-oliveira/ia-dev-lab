# ADR 0003 - Harness de Desenvolvimento

* **Status:** Aceito
* **Data:** 2026-09-05
* **Decisão:** Ferramentas e limites do harness de desenvolvimento (hooks locais, CI e bloqueio técnico de push por IA).

## Contexto

Antes de implementar a pipeline de Player Modeling em `src/`, `docs/escopo.md` (seção 2) define a necessidade de um harness de desenvolvimento: hooks de pré-commit, validação de mensagem de commit e de branch, checagem de arquivos sensíveis, CI e controle sobre operações git executadas por agentes de IA. A ADR 0002 já define o fluxo de branches (`feature/* → dev → main`) e o padrão de mensagens de commit; esta ADR registra as ferramentas escolhidas para impor esses padrões tecnicamente, e os limites desse harness.

O repositório não possuía, até este ponto, nenhuma configuração de lint, testes automatizados em CI ou hooks — o harness parte de uma base vazia (greenfield).

## Decisão

### Gerenciamento de dependências: Poetry

Adotado [Poetry](https://python-poetry.org/) (`pyproject.toml` + `poetry.lock`) no lugar do par `requirements.txt` + `venv` manual. O virtualenv é criado pelo próprio Poetry (nunca manualmente) e fixado em `./.venv/`, dentro do projeto, via `poetry.toml` (`virtualenvs.in-project = true`) — decisão explícita para facilitar a detecção do interpretador por editores.

### Lint e formatação: Ruff

Adotado [Ruff](https://docs.astral.sh/ruff/) no lugar da combinação `flake8` + `black` + `isort`: uma única ferramenta, mais rápida em pre-commit, com configuração única em `pyproject.toml`.

### Verificação de tipos: mypy

Adotado `mypy`, com configuração inicial permissiva fora de `src/player_modeling/` (onde ainda não há código) e obrigatória para o novo código desse pacote conforme a pipeline for implementada.

### Orquestração dos hooks: framework `pre-commit`

Os hooks são definidos em `.pre-commit-config.yaml` (framework [pre-commit](https://pre-commit.com/)), cobrindo: Ruff (lint + formatação), mypy, testes rápidos (`pytest`), validação da mensagem de commit (`scripts/check_commit_message.py`, estágio `commit-msg`), validação da branch atual (`scripts/check_branch.py`) e detecção de arquivos sensíveis (`scripts/check_sensitive_paths.py`, mais os hooks prontos `detect-private-key` e `check-added-large-files`).

### CI: GitHub Actions restrito a testes unitários em PRs para dev

O workflow `.github/workflows/ci.yml` dispara apenas em Pull Requests cuja branch de destino é `dev`, e roda somente a suíte de testes unitários (`pytest`) em ambiente limpo — sem lint/mypy (garantidos localmente pelo pre-commit) e sem proteção de branch remota configurada nesta change.

### Bloqueio técnico de push automático por agentes de IA

Um hook `PreToolUse` do Claude Code (`.claude/settings.json`, script `scripts/block_git_push_hook.py`) bloqueia incondicionalmente qualquer comando Bash que invoque `git push`, mesmo quando solicitado explicitamente na conversa. `git commit` e `git merge` locais pelo agente **não** são bloqueados — apenas o envio de alterações ao repositório remoto exige uma ação manual do desenvolvedor.

### Relatório de alterações fora do escopo

`scripts/report_scope_diff.py` lista, de forma apenas informativa (nunca bloqueante), os arquivos alterados em relação à branch base (`dev`) e sinaliza alterações em `data/events.csv`/`data/sessions_features.csv`.

## Justificativa

As ferramentas foram escolhidas para minimizar a superfície de configuração (Ruff substitui três ferramentas por uma) e para reaproveitar exatamente a mesma configuração local e em CI (`pre-commit run --all-files`), evitando divergência entre o que passa localmente e o que é validado no Pull Request.

O bloqueio de `git push` via hook do Claude Code foi a solução técnica encontrada porque um git hook tradicional (`pre-push`) não consegue distinguir se o comando foi disparado pelo agente de IA ou diretamente pelo desenvolvedor no terminal — apenas o `PreToolUse` do Claude Code, que intercepta a chamada da ferramenta Bash antes da execução, permite essa distinção. `git commit` e `git merge` locais foram deliberadamente deixados fora do bloqueio: eles não afetam o repositório remoto nem terceiros, e bloqueá-los tornaria o fluxo de trabalho com o agente impraticável sem nenhum ganho de segurança adicional.

Não foi configurada proteção de branch remota (`main`/`dev`) no GitHub nesta change — decisão explícita do desenvolvedor para manter o escopo restrito a testes unitários em CI e ao controle sobre o agente de IA, deixando eventual proteção de branch remota para uma change futura, caso se mostre necessária.

## Consequências

### Positivas

* Lint, tipos e testes ficam garantidos tanto localmente (pre-commit) quanto em CI, com a mesma configuração.
* Mensagens de commit e branches seguem a ADR 0002 de forma verificável, não apenas por convenção.
* O push para o repositório remoto nunca é feito automaticamente por um agente de IA, mesmo que solicitado.

### Negativas / Limites

* Hooks locais podem ser contornados com `git commit --no-verify`; como não há proteção de branch remota, esse é um risco aceito nesta change.
* A detecção de arquivos sensíveis é baseada em padrões de caminho/nome, não em análise de conteúdo — não substitui uma auditoria de segurança completa.
* O bloqueio de `git push` é uma configuração do Claude Code (`.claude/settings.json`); não impede o desenvolvedor de dar push manualmente no terminal (comportamento desejado) nem se aplica a outros agentes de IA fora do Claude Code.
