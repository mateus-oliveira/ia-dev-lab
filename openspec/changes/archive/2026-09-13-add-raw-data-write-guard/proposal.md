## Why

O `CLAUDE.md` define, na seção "Não fazer", uma regra explícita de dados: `src/data/events.csv` e `src/data/sessions_features.csv` são **dados de origem** — o dataset sintético rotulado que pré-treina o classificador de personas (ADR 0010) — e "não devem ser editados manualmente nem sobrescritos pelo pipeline"; a única forma sancionada de regenerá-los é `src/player_modeling/scripts/generate_raw_events.py`.

Hoje essa regra é apenas textual. O harness (ADR 0003) tem um único controle técnico sobre o agente de IA: o hook `PreToolUse` que bloqueia `git push`. Nada impede o agente de reescrever, truncar ou apagar os CSVs de origem com uma chamada de `Write`, `Edit` ou um `Bash` com redirecionamento (`> src/data/events.csv`), `sed -i`, `rm` ou `mv`. O impacto é silencioso e difícil de perceber: qualquer alteração nesses arquivos muda o dataset de treino e, portanto, o modelo servido pela API, sem que nenhum teste falhe — os testes de `ml/knn.py` verificam limiares de acurácia, não a integridade do dataset. `scripts/report_scope_diff.py` sinaliza alterações nesses arquivos, mas é deliberadamente informativo e roda **depois** do estrago.

Este é um risco específico deste projeto (corrupção da fonte de verdade do treino do modelo), distinto do risco genérico de operações git já coberto pelo harness.

## What Changes

- **Novo hook `PreToolUse` (`scripts/block_raw_data_write_hook.py`)**: bloqueia, antes da execução, qualquer chamada de ferramenta do agente de IA que escreva nos arquivos de dados de origem protegidos (`src/data/events.csv`, `src/data/sessions_features.csv`), devolvendo código de saída 2 e uma mensagem explicando a regra e o caminho sancionado (`generate_raw_events.py`).
- **Cobertura por ferramenta**: `Write`, `Edit` e `NotebookEdit` são avaliados pelo `file_path` do payload; `Bash` é avaliado pelo texto do comando, detectando redirecionamento (`>`, `>>`) para um arquivo protegido e utilitários de escrita/remoção (`rm`, `mv`, `cp`, `tee`, `truncate`, `dd`, `sed -i`) aplicados a um arquivo protegido.
- **Leitura continua livre**: `cat`, `head`, `grep`, `wc`, `pandas.read_csv` e qualquer outra leitura dos CSVs permanecem permitidas — o hook bloqueia escrita, não acesso.
- **Caminho sancionado preservado**: executar `src/player_modeling/scripts/generate_raw_events.py` continua permitido, ainda que o script regrave os CSVs; o hook bloqueia a edição direta, não a regeneração oficial documentada no `CLAUDE.md`.
- **Registro em `.claude/settings.json`**: o novo hook é adicionado ao evento `PreToolUse` com matcher cobrindo `Write|Edit|NotebookEdit|Bash`, ao lado do hook de `git push` existente.
- **Testes (`src/tests/scripts/test_block_raw_data_write_hook.py`)**: espelham o módulo em `scripts/`, conforme a convenção de testes do `CLAUDE.md`.
- **Documentação**: `README.md`, `CLAUDE.md` e a ADR 0003 passam a descrever os dois controles técnicos sobre o agente, não apenas o bloqueio de `git push`.
- **Fora de escopo**: proteção de `.env`/segredos (já parcialmente coberta por `check_sensitive_paths.py` e `detect-private-key`); proteção de `db.sqlite3` ou de migrações Alembic; qualquer bloqueio que se aplique ao desenvolvedor digitando no terminal (o hook é do Claude Code e alcança apenas o agente); proteção contra outros agentes de IA fora do Claude Code.

## Capabilities

### New Capabilities
- `harness/raw-data-write-guard`: bloqueia tecnicamente, antes da execução da ferramenta, escritas do agente de IA nos arquivos de dataset de origem do projeto.

### Modified Capabilities
(nenhuma — não há capacidade de spec existente sendo alterada.)

## Impact

- **Código**: novo `scripts/block_raw_data_write_hook.py` e novo `src/tests/scripts/test_block_raw_data_write_hook.py`.
- **Configuração**: `.claude/settings.json` ganha uma segunda entrada em `PreToolUse`.
- **Fluxo de trabalho com o agente**: o agente deixa de conseguir alterar os CSVs de origem, mesmo quando solicitado explicitamente na conversa; regenerar o dataset passa a exigir o script oficial.
- **Documentação**: `README.md`, `CLAUDE.md` e `docs/adr/0003-harness-desenvolvimento.md`.
- **Dependências**: nenhuma nova (Python puro, biblioteca padrão).
