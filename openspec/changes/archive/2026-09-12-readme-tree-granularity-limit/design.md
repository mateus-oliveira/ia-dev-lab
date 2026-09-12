## Context

`README.md` documenta a estrutura do projeto com uma árvore ASCII dentro de um bloco ```` ```text ```` (seção "Estrutura do projeto", ver `README.md`). Hoje essa árvore lista manualmente cada arquivo `.py`/`.md`/`.csv` folha de `docs/adr/`, `scripts/` e de todos os subdiretórios de `src/` (ver proposal.md - Why). O harness do projeto já roda checagens de pré-commit locais em Python puro (ADR 0003), registradas em `.pre-commit-config.yaml` como hooks `repo: local`, cada uma com um script correspondente em `scripts/` e teste espelhado em `src/tests/scripts/` (ex.: `check_sensitive_paths.py`).

## Goals / Non-Goals

**Goals:**
- Definir uma regra de granularidade simples, objetiva e fácil de verificar mecanicamente para a árvore de diretórios do README.
- Implementar essa verificação como hook de pré-commit local, seguindo o mesmo padrão dos hooks existentes (script standalone em `scripts/`, sem dependências novas).
- Deixar a árvore atual do README em conformidade com a nova regra.

**Non-Goals:**
- Não é objetivo gerar a árvore do README automaticamente a partir do sistema de arquivos (isso seria uma solução mais robusta, mas adiciona complexidade e acoplamento não solicitados; ver "Alternativas" abaixo).
- Não é objetivo validar nenhum outro aspecto do conteúdo do README além do bloco de árvore de diretórios.
- Não é objetivo verificar a tabela "Organização dos diretórios" (linhas 141-155 do README atual) - ela já é curada manualmente por diretório e não cresce por arquivo.

## Decisions

### Regra de granularidade: apenas diretórios + arquivos de raiz

A árvore pode listar diretórios em qualquer profundidade (ex.: `src/player_modeling/worker/`) e arquivos apenas quando estão diretamente na raiz do projeto (profundidade 1: `CLAUDE.md`, `README.md`, `docker-compose.yml`, `Makefile`, etc.). Nenhum arquivo dentro de um subdiretório pode aparecer individualmente, independentemente de "importância" percebida (isso inclui ADRs em `docs/adr/`, que também crescem sem limite ao longo do tempo).

Alternativas consideradas:
- *Permitir uma lista de exceções por caminho (allowlist)*: adiciona um segundo lugar para manter atualizado e reintroduz o mesmo problema de escala que esta change busca eliminar. Rejeitada.
- *Gerar a árvore automaticamente a partir do `git ls-tree` e substituir o bloco no README a cada commit*: resolve o problema de forma mais completa, mas é uma mudança de comportamento maior (README passa a ser gerado, não editado à mão) e não foi solicitada; pode ser proposta como change futura se a regra de granularidade não for suficiente. Rejeitada por ora.
- *Regra por profundidade de diretório (não apenas raiz)*: por exemplo, "arquivos até profundidade 2 são permitidos". Mais permissiva, mas ainda escala mal (ex.: `docs/adr/*.md` está em profundidade 2 e continuaria crescendo sem limite). A regra "só raiz" escolhida é a mais simples de enunciar, implementar e justificar.

### Implementação: parser de indentação do bloco de árvore ASCII

O script (`scripts/check_readme_tree_granularity.py`) localiza o bloco ```` ```text ```` que contém a árvore (identificado por conter a primeira linha terminada em `/` seguida do nome do diretório raiz do projeto) e, para cada linha subsequente até o fechamento ```` ``` ````, calcula a profundidade a partir do prefixo de indentação da árvore ASCII (caracteres `│`, espaços e o conector `├──`/`└──`) e verifica:
- se a linha representa um diretório (termina em `/`) → sempre permitido;
- se a linha representa um arquivo e a profundidade calculada é 1 (imediatamente abaixo da raiz) → permitido;
- se a linha representa um arquivo em profundidade ≥ 2 → violação.

Isso evita qualquer dependência nova: é manipulação de string pura, como os outros hooks locais do projeto.

### Hook e testes seguem o padrão existente

Novo hook `repo: local` em `.pre-commit-config.yaml`, entry `poetry run python scripts/check_readme_tree_granularity.py`, mesmo estilo de `check-sensitive-paths`. Teste em `src/tests/scripts/test_check_readme_tree_granularity.py`, cobrindo: árvore válida, árvore com arquivo em subdiretório (deve falhar), README sem bloco de árvore (não deve quebrar/aplicar-se), e a árvore real atual do README após a correção (regressão).

## Risks / Trade-offs

- [O parser depende do formato exato da árvore ASCII gerada manualmente (ex.: uso de `│`, `├──`, `└──`, 4 espaços por nível)] → Mitigação: documentar o formato esperado no docstring do script e na ADR; se o formato divergir, o hook deve falhar de forma explícita (erro claro) em vez de silenciosamente deixar de verificar.
- [Regra pode parecer rígida ao impedir listar um arquivo específico que o desenvolvedor considera importante dentro de um subdiretório] → Mitigação: a ADR documenta que "importância" deve ser comunicada pela tabela "Organização dos diretórios" (por diretório) ou por um ADR próprio, não pela árvore de arquivos.

## Migration Plan

1. Criar o script de verificação e seus testes.
2. Registrar o hook em `.pre-commit-config.yaml`.
3. Reescrever o bloco de árvore do `README.md` para conformidade (colapsar `docs/adr/`, `scripts/`, e todos os subdiretórios de `src/` para não listarem arquivos).
4. Rodar `poetry run pre-commit run --all-files` para confirmar que o novo hook passa com o README já corrigido.
5. Criar a ADR documentando a decisão.

Rollback: remover a entrada do hook em `.pre-commit-config.yaml` e o script em `scripts/`; não há estado persistente ou migração de dados envolvida.
