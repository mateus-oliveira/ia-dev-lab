## 1. Hook de bloqueio

- [x] 1.1 Criar `scripts/block_raw_data_write_hook.py` com a constante dos caminhos protegidos (`src/data/events.csv`, `src/data/sessions_features.csv`) e a normalização de caminho descrita no `design.md`, verificando com `poetry run python -c "import scripts.block_raw_data_write_hook"` que o módulo importa sem efeito colateral.
- [x] 1.2 Implementar a avaliação das ferramentas de edição (`Write`, `Edit`, `NotebookEdit`) a partir de `tool_input.file_path`, verificando por teste que um caminho protegido é bloqueado e um caminho qualquer de `src/` é permitido.
- [x] 1.3 Implementar a avaliação de `Bash` (redirecionamento `>`/`>>` e utilitários de escrita) reaproveitando a tokenização por `shlex`, verificando por teste os cenários de bloqueio (`> src/data/events.csv`, `rm`, `mv`, `sed -i`) e de permissão (`cat`, `head`, `grep`, `wc`).
- [x] 1.4 Implementar `main()` seguindo o protocolo de hooks do Claude Code (lê JSON de `stdin`, devolve 2 com mensagem em `stderr` para bloquear, 0 para permitir; payload malformado devolve 0), verificando por teste os três casos.

## 2. Registro no harness

- [x] 2.1 Adicionar o hook ao evento `PreToolUse` em `.claude/settings.json` com matcher `Write|Edit|NotebookEdit|Bash`, preservando o hook de `git push` existente, e verificar o JSON com `poetry run python -c "import json; json.load(open('.claude/settings.json'))"`.

## 3. Testes automatizados

- [x] 3.1 Criar `src/tests/scripts/test_block_raw_data_write_hook.py` espelhando a convenção dos testes de harness existentes, cobrindo: bloqueio por `file_path`, bloqueio por redirecionamento, bloqueio por utilitário de escrita, permissão de leitura, permissão do script oficial `generate_raw_events.py`, normalização de caminho (`./`, absoluto) e payload malformado.
- [x] 3.2 Executar `poetry run pytest src/tests/scripts/test_block_raw_data_write_hook.py` e depois a suíte completa (`poetry run pytest`), confirmando que nada existente quebrou.

## 4. Evidência do bloqueio (Etapa 1 da atividade)

- [x] 4.1 Disparar deliberadamente a ação bloqueada (tentativa real de escrita em `src/data/events.csv` pelo agente) e registrar a saída do bloqueio em `docs/aula6/etapa1-autonomia-e-hook.md`, confirmando com `git status --short src/data/` que o arquivo permaneceu intacto.

## 5. Qualidade e documentação

- [x] 5.1 Rodar `poetry run ruff check .`, `poetry run ruff format .` e `poetry run mypy .`, corrigindo apontamentos.
- [x] 5.2 Atualizar `README.md`, `CLAUDE.md` e `docs/adr/0003-harness-desenvolvimento.md` para descrever os dois controles `PreToolUse` sobre o agente, verificando o resultado com `git diff`.
- [x] 5.3 Executar `poetry run python scripts/report_scope_diff.py dev` e confirmar que não há alterações em `src/data/`.
