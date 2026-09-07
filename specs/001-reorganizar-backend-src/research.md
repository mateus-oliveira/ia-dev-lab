# Phase 0 Research: Reorganizar artefatos do backend sob src/

Nenhum marcador `[NEEDS CLARIFICATION]` foi deixado na spec ou no Technical Context do plano. Este documento registra as decisões de projeto tomadas a partir do estado real do repositório (inspecionado antes da escrita da spec), não de pesquisa externa.

## Decisão 1: Onde colocar `generate_raw_events.py` dentro de `src/`

- **Decision**: Mover para `src/player_modeling/scripts/generate_raw_events.py`.
- **Rationale**: O script gera o dataset sintético (`data/events.csv`, `data/sessions_features.csv`) usado para pré-treinar o modelo de ML do domínio `player_modeling`. `CLAUDE.md` pede organização "por domínio ou funcionalidade, e não apenas por tipo técnico" — colocar o script dentro do pacote de domínio que ele alimenta é mais coerente do que um `src/scripts/` genérico e técnico.
- **Alternatives considered**:
  - `src/scripts/generate_raw_events.py` — rejeitado por criar uma categoria técnica genérica dentro de `src/`, indo contra a preferência do projeto por organização por domínio.
  - Manter em `scripts/` na raiz — rejeitado porque é exatamente o problema que o item 4 do escopo pede para resolver (mistura de script de pipeline com scripts de harness).

## Decisão 2: Como tornar rastreáveis os diretórios de domínio hoje vazios

- **Decision**: Adicionar um `__init__.py` com uma docstring de uma linha por diretório (`api`, `ml`, `simulator`, `worker`, e o pacote `player_modeling` em si), em vez de `.gitkeep`.
- **Rationale**: Diretórios vazios não são versionados pelo Git. Usar `__init__.py` (em vez de `.gitkeep`) já prepara os diretórios como pacotes Python importáveis, que é o que serão quando a pipeline for implementada (fora do escopo desta feature), evitando um passo extra futuro.
- **Alternatives considered**:
  - `.gitkeep` — mais comum para diretórios genéricos, mas não comunica que o diretório é um pacote Python nem documenta seu propósito.
  - Não versionar os diretórios agora, criando-os apenas quando a implementação real começar — rejeitado porque o item 4 do escopo pede explicitamente uma "estrutura interna coerente" documentada agora, antes da pipeline.

## Decisão 3: Compatibilidade de execução do script após a mudança de caminho

- **Decision**: Nenhuma mudança de código é necessária no script. `generate_raw_events.py` não faz imports internos do projeto (só stdlib) e resolve `--outdir` como caminho relativo ao diretório de trabalho atual (`data`, não relativo ao arquivo). Executá-lo a partir da raiz do repositório com `poetry run python src/player_modeling/scripts/generate_raw_events.py --players 200 --seed 42` produz exatamente a mesma saída em `data/` que antes.
- **Rationale**: Confirmado lendo o código-fonte do script (uso de `os.makedirs(args.outdir, ...)` e `os.path.join(args.outdir, ...)`, com `default="data"`).
- **Alternatives considered**: Empacotar o script como entry point do Poetry (`[tool.poetry.scripts]`) — considerado desnecessário para o escopo desta feature (não pedido pelo item 4) e adiado para não introduzir mudança de comportamento além da reorganização de arquivos.
