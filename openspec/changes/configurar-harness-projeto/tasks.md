## 1. Base de dependências e configuração de ferramentas (Poetry)

- [x] 1.1 Inicializar `pyproject.toml` com Poetry (metadados do projeto, Python 3.13) e o grupo de dependências `dev` contendo `ruff`, `mypy`, `pytest` e `pre-commit`; criar `poetry.toml` versionado na raiz com `virtualenvs.in-project = true`; verificar que `poetry install` conclui sem erro, gera `poetry.lock` e cria o virtualenv em `./.venv/` (não no cache global do Poetry, e sem nenhuma venv criada manualmente)
- [x] 1.2 Adicionar `.venv` ao `.gitignore` (mantendo `venv` já existente) e verificar que `git status` não lista arquivos do virtualenv como não rastreados
- [x] 1.3 Adicionar configuração do Ruff (lint + formatação) em `pyproject.toml` e verificar que `poetry run ruff check .` e `poetry run ruff format --check .` executam sem erro de configuração no repositório atual
- [x] 1.4 Adicionar configuração do mypy em `pyproject.toml`, permissiva para código ainda não tipado fora de `src/player_modeling/`, e verificar que `poetry run mypy .` executa sem erro de configuração
- [x] 1.5 Adicionar configuração básica do pytest em `pyproject.toml` e verificar que `poetry run pytest` roda (mesmo sem testes coletados) sem erro

## 2. Hooks de pré-commit (qualidade de código)

- [x] 2.1 Criar `.pre-commit-config.yaml` com os hooks do Ruff (lint + format) e mypy, e verificar que `poetry run pre-commit run ruff --all-files` e `poetry run pre-commit run mypy --all-files` executam com sucesso no estado atual do repositório
- [x] 2.2 Adicionar um hook de testes rápidos (`pytest`) ao `.pre-commit-config.yaml`, cobrindo o cenário "commit com testes passando" e "commit com testes falhando" de `specs/dev-harness/spec.md` (Requirement: Verificação de qualidade antes do commit), e verificar manualmente os dois cenários com um teste de exemplo temporário
- [x] 2.3 Instalar os hooks localmente com `poetry run pre-commit install` e documentar o comando no README, verificando que um commit com código propositalmente mal formatado é bloqueado e um commit com código formatado corretamente é aceito

## 3. Validação de mensagem de commit

- [x] 3.1 Criar `scripts/check_commit_message.py`, validando o padrão `<PREFIXO>: <descrição>` da ADR 0002 (`ADD`, `UPDATE`, `FIX`, `REMOVE`, `REFACTOR`, `DOCS`, `TEST`)
- [x] 3.2 Escrever testes unitários em `tests/` para `check_commit_message.py` cobrindo mensagens válidas e inválidas (cenários da Requirement "Validação da mensagem de commit"), e verificar que `poetry run pytest tests/test_check_commit_message.py` passa
- [x] 3.3 Registrar o script como hook `commit-msg` no `.pre-commit-config.yaml` e verificar manualmente que um commit com mensagem fora do padrão é rejeitado e um commit com prefixo válido é aceito

## 4. Validação da branch atual

- [x] 4.1 Criar `scripts/check_branch.py` que identifica a branch atual e sinaliza/bloqueia quando for `main` ou `dev`, cobrindo os cenários da Requirement "Validação da branch atual"
- [x] 4.2 Escrever testes unitários para `check_branch.py` (branch de tarefa válida vs. `main`/`dev`), e verificar que `poetry run pytest tests/test_check_branch.py` passa
- [x] 4.3 Registrar `check_branch.py` como hook local (`pre-commit`) no `.pre-commit-config.yaml` e verificar manualmente o bloqueio ao tentar commitar estando em `main` ou `dev` localmente

## 5. Detecção de arquivos sensíveis

- [x] 5.1 Adicionar ao `.pre-commit-config.yaml` os hooks prontos do `pre-commit-hooks` relevantes (`detect-private-key`, `check-added-large-files`) e verificar que rodam sem erro sobre o repositório atual
- [x] 5.2 Criar `scripts/check_sensitive_paths.py` bloqueando arquivos staged que casem com padrões de `.env*`, diretórios de venv (`venv/`, `.venv/`) e artefatos de execução (`__pycache__/`, `*.pyc`), conforme a Requirement "Detecção de arquivos sensíveis"
- [x] 5.3 Escrever testes unitários para `check_sensitive_paths.py` cobrindo os dois cenários da spec (sem arquivos sensíveis vs. com arquivo sensível), e verificar que `poetry run pytest tests/test_check_sensitive_paths.py` passa
- [x] 5.4 Registrar `check_sensitive_paths.py` no `.pre-commit-config.yaml` e verificar manualmente que um commit tentando adicionar um `.env` de teste é bloqueado

## 6. Relatório de alterações fora do escopo

- [x] 6.1 Criar `scripts/report_scope_diff.py`, comparando a branch atual com `dev` (branch de origem) e listando arquivos alterados, sinalizando explicitamente `data/events.csv`, `data/sessions_features.csv` ou outros caminhos fora do padrão esperado de uma tarefa
- [x] 6.2 Escrever testes unitários para `report_scope_diff.py` cobrindo os dois cenários da spec (alterações dentro do escopo vs. alteração em dado bruto/fora do escopo), e verificar que `poetry run pytest tests/test_report_scope_diff.py` passa
- [x] 6.3 Documentar no README/CLAUDE.md o comando para rodar o relatório antes de finalizar uma tarefa

## 7. CI de testes unitários em Pull Requests para dev

- [x] 7.1 Criar `.github/workflows/ci.yml`, disparado em `pull_request` apenas quando a branch de destino (`base`) é `dev`, que instala o Poetry e roda `poetry install` usando o `poetry.lock` versionado
- [x] 7.2 Adicionar ao mesmo workflow o passo `poetry run pytest` (suíte completa de testes unitários), e verificar que o workflow não é disparado para Pull Requests direcionados a `main` ou outra branch
- [ ] 7.3 Abrir um Pull Request de verificação (branch `chore/*` → `dev`) para confirmar que o workflow é disparado e reporta status de sucesso/falha corretamente para os cenários "Pull Request para dev com todos os testes passando" e "Pull Request para dev com testes falhando" da Requirement "CI executa a suíte de testes em Pull Requests para dev"

## 8. Bloqueio técnico de push automático por agentes de IA

- [x] 8.1 Adicionar a `.claude/settings.json` (versionado no repositório) um hook `PreToolUse` para a ferramenta Bash que casa comandos contendo `git push` e nega (`deny`) a execução incondicionalmente, com mensagem indicando que o push deve ser feito manualmente pelo desenvolvedor; `git commit` e `git merge` locais não devem ser bloqueados
- [ ] 8.2 Verificar manualmente, em uma sessão do Claude Code neste repositório, que uma tentativa do agente de executar `git push` via Bash é bloqueada pelo hook, inclusive quando solicitado explicitamente na conversa, e que `git commit`/`git merge` locais continuam permitidos, cobrindo os cenários da Requirement "Bloqueio técnico de push automático por agentes de IA"
- [ ] 8.3 Verificar manualmente que o desenvolvedor ainda consegue executar `git push` diretamente no terminal (fora da automação do agente), sem ser afetado pelo hook

## 9. Documentação e ADR

- [ ] 9.1 Criar `docs/adr/0003-harness-desenvolvimento.md` registrando as decisões de `design.md` (Poetry, Ruff, mypy, framework pre-commit, CI restrito a testes unitários em PRs para dev, hook de bloqueio de push automático) e referenciando a ADR 0002
- [ ] 9.2 Atualizar a seção "Comandos" do `CLAUDE.md` (e o README) substituindo `python3.13 -m venv venv` / `pip install -r requirements.txt` por `poetry install`, e documentando `poetry run pre-commit install`, `poetry run ruff check .`, `poetry run mypy .`, `poetry run pytest` e o comando do relatório de escopo
- [ ] 9.3 Atualizar `README.md`/`CLAUDE.md` documentando o hook de bloqueio de push automático por IA, conforme a Requirement "Bloqueio técnico de push automático por agentes de IA"

## 10. Verificação integrada do harness

- [ ] 10.1 Rodar `poetry run pytest` e `poetry run pre-commit run --all-files` no repositório final e verificar que todos os hooks e testes descritos em `specs/dev-harness/spec.md` passam
- [ ] 10.2 Revisar manualmente os cenários de `specs/dev-harness/spec.md` que não são cobertos por teste automatizado (CI disparado corretamente em PR para dev; bloqueio de push automático por IA) e confirmar seu comportamento observado
