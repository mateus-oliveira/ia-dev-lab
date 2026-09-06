## Context

O repositório está praticamente vazio de código (`src/`, `tests/` sem arquivos; nenhum `requirements*.txt`, `pyproject.toml`, `.github/` ou configuração de pre-commit ainda existe). Já existem: ADR 0002 (fluxo de branches `feature/* → dev → main` e prefixos de commit), `docs/escopo.md` seção 2 (lista dos controles exigidos) e um remote GitHub (`git@github.com:mateus-oliveira/ia-dev-lab.git`) com as branches `main` e `dev`. Isso é greenfield para o harness: não há débito técnico de ferramentas concorrentes para migrar, mas também não há nenhum baseline de lint/testes para herdar.

Ver `proposal.md` (Why / What Changes) para a motivação; ver `specs/dev-harness/spec.md` para o contrato de comportamento exigido de cada controle.

## Goals / Non-Goals

**Goals:**
- Escolher um conjunto mínimo e coeso de ferramentas para lint, formatação, verificação de tipos e testes, reaproveitado tanto localmente (pre-commit) quanto em CI.
- Definir onde cada controle da spec roda (hook local vs. CI vs. configuração do Claude Code) e como cada um reporta falha.

**Non-Goals:**
- Não escolher ferramentas de lint/tipo/teste específicas para a futura pipeline de Player Modeling além do necessário para o harness em si (ex.: dependências de ML não entram aqui).
- Não implementar um scanner de segredos genérico e pesado (ex.: verificação de entropia em todo o histórico); o objetivo é bloquear os casos objetivos listados na spec (`.env`, chaves privadas, diretórios de venv), não substituir uma auditoria de segurança completa.
- Não configurar proteção de branch no GitHub remoto nem CI de deploy — CI cobre apenas testes unitários em Pull Requests para `dev`.

## Decisions

### Gerenciamento de dependências: Poetry
**Decisão:** usar [Poetry](https://python-poetry.org/) (`pyproject.toml` + `poetry.lock`) como gerenciador de dependências e de ambiente, substituindo o par `requirements.txt` + `venv` manual mencionado hoje no `CLAUDE.md`/`README.md`.
**Motivo:** um único `pyproject.toml` concentra metadados do projeto, dependências de execução e de desenvolvimento (grupo `dev`: ruff, mypy, pytest, pre-commit), com `poetry.lock` garantindo que ambiente local e CI instalem exatamente as mesmas versões (`poetry install` / `poetry install --sync`) — cobrindo a Requirement "Reprodutibilidade das dependências de desenvolvimento" sem precisar manter `requirements.txt` e `requirements-dev.txt` em paralelo. Trade-off aceito: introduz uma ferramenta adicional (o binário `poetry`) como pré-requisito de ambiente, documentada no README/CLAUDE.md; considerado aceitável porque centraliza também a configuração do Ruff/mypy/pytest no mesmo arquivo.
**Impacto no `CLAUDE.md`:** a seção "Comandos" (`python3.13 -m venv venv`, `pip install -r requirements.txt`) deve ser atualizada para `poetry install` e `poetry run <comando>` como parte desta change (ver tasks.md, grupo 9).
**Local do virtualenv:** o Poetry SEMPRE cria e usa um virtualenv isolado automaticamente (nunca instala pacotes no Python global) — isso é o comportamento padrão independente de configuração. O que varia é apenas onde esse virtualenv fica. Por decisão explícita do desenvolvedor, o projeto SHALL configurar `virtualenvs.in-project = true` via um `poetry.toml` versionado na raiz do repositório, para que `poetry install` crie o virtualenv em `./.venv/` (dentro do projeto, facilitando a detecção automática do interpretador por editores) em vez do cache global padrão do Poetry. Nenhuma venv deve ser criada manualmente (`python3.13 -m venv ...`) — a criação é sempre feita pelo `poetry install`. `.venv/` SHALL ser adicionado ao `.gitignore` e SHALL ser coberto pelo controle de arquivos sensíveis (`scripts/check_sensitive_paths.py`, ver Requirement "Detecção de arquivos sensíveis").

### Lint e formatação: Ruff
**Decisão:** usar [Ruff](https://docs.astral.sh/ruff/) para lint e formatação, em vez da combinação `flake8` + `black` + `isort`.
**Motivo:** uma única dependência binária (sem plugins para gerenciar), muito mais rápida em pre-commit (importante porque o hook roda a cada commit), e cobre lint + formatação + ordenação de imports com uma config única em `pyproject.toml`. Trade-off aceito: é uma ferramenta mais nova, com menos anos de maturidade que `flake8`/`black`, mas já é o padrão de facto em projetos Python novos e reduz a superfície de configuração.

### Verificação de tipos: mypy
**Decisão:** usar `mypy` para checar os type hints exigidos pelo `CLAUDE.md`.
**Motivo:** é a ferramenta de type-checking mais estabelecida para Python e integra-se facilmente ao `pre-commit` e ao CI. Alternativa considerada: `pyright` (mais rápido, mas orientado ao ecossistema Node/VS Code e menos padrão em pipelines pytest/CI Python puro). Como ainda não há código em `src/`, a configuração inicial do mypy será permissiva o suficiente para não travar módulos ainda não tipados incrementalmente, mas obrigatória para qualquer novo código sob `src/player_modeling/`.

### Orquestração dos hooks: framework `pre-commit`
**Decisão:** usar o framework [pre-commit](https://pre-commit.com/) (`.pre-commit-config.yaml`) em vez de scripts manuais em `.git/hooks/`.
**Motivo:** versiona a configuração dos hooks junto do código (`.pre-commit-config.yaml`), permite reexecutar exatamente os mesmos hooks em CI (`pre-commit run --all-files`), e já fornece hooks prontos (`check-added-large-files`, `detect-private-key`, `check-merge-conflict`) reaproveitados pelo controle de arquivos sensíveis, evitando reimplementar verificações genéricas.
**Estágios usados:**
- `pre-commit` (stage padrão): Ruff (lint + format --check), mypy, testes rápidos, checagem de arquivos sensíveis, checagem de branch atual.
- `commit-msg`: hook local (script Python) que valida o padrão `<PREFIXO>: <descrição>` da ADR 0002.

### Testes rápidos vs. suíte completa
**Decisão:** os testes executados no hook de pré-commit são os marcados/selecionados como rápidos (ex.: `pytest -m "not slow"` ou, na ausência de testes lentos, a suíte inteira quando ela for pequena o suficiente); a suíte completa sempre roda no CI.
**Motivo:** manter o pre-commit rápido o bastante para não ser contornado por impaciência, sem abrir mão de cobertura completa antes do merge (CI). Quando a suíte crescer e ficar lenta para pre-commit, uma marca `@pytest.mark.slow` deve ser adotada — não é necessário decidir isso agora porque não há testes ainda.

### Verificação de arquivos sensíveis: hooks objetivos, não heurística de conteúdo
**Decisão:** bloquear por padrão de caminho/nome (`.env*`, `venv/`, `.venv/`, chaves privadas via `detect-private-key` do `pre-commit-hooks`, artefatos de execução como `__pycache__/`, `*.pkl`, `*.joblib` fora de um diretório de modelos versionado) em vez de tentar detectar heuristicamente "dados pessoais" no conteúdo dos arquivos.
**Motivo:** detecção de conteúdo sensível por heurística gera falsos positivos/negativos difíceis de justificar; os dados do projeto já são sintéticos por definição (`docs/escopo.md`), então o risco real é versionar acidentalmente um `.env`, uma chave ou um ambiente virtual — casos objetivos e determinísticos de checar.

### CI: GitHub Actions, restrito a testes unitários em PRs para dev
**Decisão:** um único workflow `.github/workflows/ci.yml`, disparado em `pull_request` apenas quando a branch de destino é `dev`, que instala o Poetry, roda `poetry install` (usando o `poetry.lock` versionado) e então `poetry run pytest` (suíte completa de testes unitários). O workflow não roda lint/mypy — esses ficam garantidos localmente pelo pre-commit.
**Motivo:** escopo definido pelo desenvolvedor: CI deve validar apenas que os testes unitários passam antes de qualquer merge para `dev`, sem depender de proteção de branch no GitHub (não configurada nesta change) nem de checks adicionais de lint/tipos em CI.

### Bloqueio técnico de commits automáticos por agentes de IA
**Decisão:** adicionar um hook `PreToolUse` para a ferramenta Bash em `.claude/settings.json`, que casa comandos contendo `git commit`, `git push` ou `git merge` e nega (`deny`) a execução incondicionalmente — inclusive quando o desenvolvedor pede isso na própria conversa —, com uma mensagem indicando que a operação deve ser feita manualmente pelo desenvolvedor.
**Motivo:** o desenvolvedor validou explicitamente que sempre fará commits manualmente após revisão; um hook `PreToolUse` é o único ponto de controle técnico disponível para interceptar a ação antes que a ferramenta Bash a execute — diferente de um git hook (`pre-commit`/`pre-push`), que não consegue distinguir se o comando `git` foi disparado pelo agente ou diretamente pelo desenvolvedor no terminal. Alternativa descartada: apenas documentar a regra em `CLAUDE.md` (como estava na primeira versão deste design) — insuficiente, pois depende do agente "lembrar" de segui-la a cada sessão, em vez de ser tecnicamente impedido.
**Limite conhecido:** o hook se aplica somente a comandos `git` disparados pela ferramenta Bash do Claude Code; não impede o desenvolvedor de commitar/pushar manualmente no terminal (isso é o comportamento desejado) nem cobre outros agentes de IA fora do Claude Code, caso venham a ser usados no projeto.

### Nova ADR
**Decisão:** registrar as escolhas acima (Ruff, mypy, pre-commit framework, limites de bloqueio automático vs. alerta) em `docs/adr/0003-harness-desenvolvimento.md`, referenciando a ADR 0002 para o fluxo de branches/commits que o harness passa a impor tecnicamente.

## Risks / Trade-offs

- **Hooks locais podem ser ignorados com `git commit --no-verify`** → Mitigação: como não há proteção de branch remota nesta change, esse bypass é um risco aceito e documentado — a suíte de testes ainda roda em CI antes do merge para `dev`, mas lint/mypy/branch/mensagem de commit ficam sujeitos à disciplina local. Se isso se mostrar insuficiente, uma change futura pode adicionar proteção de branch remota.
- **mypy pode ser excessivamente rígido conforme o código cresce sem tipagem completa** → Mitigação: configuração inicial permissiva (ex.: `disallow_untyped_defs` ativado apenas para `src/`, não para scripts utilitários), revisitada quando a pipeline em `src/` começar a ser implementada.
- **Checagem de arquivos sensíveis por padrão de caminho pode não pegar um segredo colado dentro de um arquivo `.py` comum** → Mitigação: documentar essa limitação explicitamente (harness cobre casos objetivos, não é um DLP completo); revisão humana continua sendo a última linha de defesa, conforme os "Limites do harness" do `docs/escopo.md`.
- **O hook de bloqueio de commit é uma configuração local do Claude Code (`.claude/settings.json`) e pode, em tese, ser removida ou sobrescrita por quem tiver acesso ao repositório** → Mitigação: versionar `.claude/settings.json` no repositório (não em `.claude/settings.local.json`, que normalmente é ignorado) para que a remoção apareça como uma alteração revisável em PR; ainda assim, o controle definitivo continua sendo o hábito do desenvolvedor de nunca pedir ao agente para commitar.
- **Ruff e mypy são checados apenas para código Python; o `docs/escopo.md` também prevê regras para TypeScript** → Fora de escopo aqui: o projeto ainda não tem código TypeScript (ver CLAUDE.md, seção "Convenções de código"); quando isso mudar, uma nova change deve estender o harness.
