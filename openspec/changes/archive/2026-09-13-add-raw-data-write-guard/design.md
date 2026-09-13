## Context

O harness do projeto (ADR 0003) já usa o evento `PreToolUse` do Claude Code para bloquear `git push` (`scripts/block_git_push_hook.py`): o hook lê o payload JSON da chamada de ferramenta em `stdin` e, ao devolver código de saída 2, impede a execução e entrega a mensagem de `stderr` ao agente como motivo da recusa. Esse é o único ponto do harness que consegue interceptar uma ação **antes** que ela aconteça — hooks de pré-commit só agem no commit, e `report_scope_diff.py` é informativo.

Os arquivos a proteger são `src/data/events.csv` e `src/data/sessions_features.csv`. Eles são lidos por `ml/knn.py` (treino do classificador no startup da API) e gerados exclusivamente por `src/player_modeling/scripts/generate_raw_events.py`.

## Goals / Non-Goals

**Goals:**
- Impedir tecnicamente que o agente de IA escreva nos CSVs de origem, por qualquer ferramenta de edição ou por shell.
- Manter leitura, análise e regeneração oficial dos datasets totalmente livres.
- Seguir exatamente o padrão do hook existente: script standalone em `scripts/`, Python puro, teste espelhado em `src/tests/scripts/`.

**Non-Goals:**
- Não é objetivo ser à prova de evasão deliberada por um agente adversarial (um comando suficientemente ofuscado — via variável de ambiente, `base64`, script intermediário — escapa da análise textual). O objetivo é impedir o acidente e a decisão automática equivocada, que é o modo de falha real.
- Não é objetivo proteger o desenvolvedor de si mesmo: o hook é do Claude Code e não intercepta comandos digitados no terminal.
- Não é objetivo generalizar para uma lista configurável de caminhos protegidos; a lista é uma constante no script, como nos demais hooks do projeto.

## Decisions

### Lista de caminhos protegidos como constante do módulo

`PROTECTED_PATHS` é uma tupla de caminhos relativos à raiz do repositório. Manter a lista no código (e não em arquivo de configuração) segue o padrão dos hooks existentes (`PROTECTED_BRANCHES` em `check_branch.py`, `VALID_PREFIXES` em `check_commit_message.py`) e mantém a alteração da política rastreável por commit e coberta por teste.

Alternativa considerada: ler os caminhos de `.claude/settings.json` ou de um YAML. Rejeitada — adiciona parsing e um segundo lugar para manter sincronizado, sem ganho nesta escala.

### Normalização de caminho antes da comparação

Um mesmo arquivo pode ser referenciado como `src/data/events.csv`, `./src/data/events.csv`, `src/data/../data/events.csv` ou por caminho absoluto. A comparação é feita sobre o caminho normalizado (`os.path.normpath`) e, quando absoluto, convertido para relativo à raiz do repositório. Caminhos absolutos fora do repositório nunca correspondem a um arquivo protegido.

### Dois modos de avaliação, conforme a ferramenta

- **Ferramentas de edição (`Write`, `Edit`, `NotebookEdit`)**: o payload traz `tool_input.file_path`. A avaliação é exata — basta normalizar e comparar. Sem falsos positivos nem falsos negativos.
- **`Bash`**: não existe `file_path`; é preciso analisar o texto do comando. A análise reaproveita a tokenização por `shlex` do hook de `git push` (que já respeita aspas) e bloqueia quando um caminho protegido aparece **e** o sub-comando é de escrita:
  - redirecionamento `>` ou `>>` imediatamente antes do caminho protegido;
  - primeiro token do sub-comando entre os utilitários de escrita/remoção (`rm`, `mv`, `cp`, `tee`, `truncate`, `dd`, `sed`, `install`, `shred`).

Alternativa considerada: bloquear qualquer comando que **mencione** um caminho protegido. Rejeitada — impediria `cat src/data/events.csv`, `head`, `grep` e `wc`, que são exatamente o uso legítimo e frequente desses arquivos durante a análise, e treinaria o desenvolvedor a desativar o hook.

### `sed` é tratado como escrita sempre, não só com `-i`

`sed -i` edita no lugar; `sed` sem `-i` apenas imprime. Ainda assim, qualquer `sed` cujo alvo seja um arquivo protegido é bloqueado, porque distinguir as duas formas exige interpretar a posição das flags e o ganho de permitir `sed` de leitura é nulo (`grep`/`head`/`cat` cobrem esse uso e continuam livres). Decisão deliberada por um falso positivo barato em vez de um falso negativo caro.

### `generate_raw_events.py` permanece permitido

O script oficial de regeneração escreve nos CSVs por dentro do processo Python, sem redirecionamento nem utilitário de escrita no comando — portanto não é bloqueado pela análise acima, sem necessidade de allowlist explícita. Esse é o comportamento desejado e está registrado nos testes como cenário: o caminho sancionado pelo `CLAUDE.md` continua funcionando.

### Payload malformado não bloqueia

Se `stdin` não contiver JSON válido ou faltarem as chaves esperadas, o hook devolve 0 (permite). Um hook de harness que quebra a sessão do agente por um payload inesperado custa mais do que o risco que evita, e o mesmo critério já é usado no hook de `git push` (que usa `.get` com padrão vazio).

## Risks / Trade-offs

- **Evasão por ofuscação**: comando montado dinamicamente (`FILE=src/data/events.csv; > $FILE`) não é detectado. Aceito e documentado como limite explícito na ADR, coerente com o limite já registrado para o hook de `git push`.
- **Falso positivo em `cp` de backup**: `cp src/data/events.csv /tmp/backup.csv` é leitura, mas o primeiro token é `cp` e o caminho protegido aparece — o comando é bloqueado. Trade-off aceito: a mensagem de erro explica a regra e o desenvolvedor pode executar o comando manualmente no terminal.
- **Configuração local**: `.claude/settings.json` é versionado, mas um clone sem Claude Code (ou outro agente) não tem o controle. Limite já conhecido do harness.

## Migration Plan

Não há migração: o hook passa a valer na próxima sessão do agente após o merge, sem efeito sobre dados ou schema.

## Open Questions

Nenhuma.
