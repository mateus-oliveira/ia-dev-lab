# harness/readme-tree-granularity Specification

## Purpose

Garante que a árvore de diretórios documentada em `README.md` permaneça sustentável à medida que o projeto cresce, impedindo que commits voltem a listar arquivos individuais de subdiretórios de código ou teste em vez de apenas diretórios e arquivos de nível raiz.

## Requirements

### Requirement: Granularidade permitida na árvore do README
A árvore de diretórios do bloco "Estrutura do projeto" em `README.md` SHALL listar apenas: (a) diretórios, em qualquer profundidade, representados com uma barra final (`/`) ou de forma inequívoca como diretório no formato de árvore ASCII usado; e (b) arquivos localizados diretamente na raiz do projeto (profundidade 1, imediatamente abaixo de `player-modeling-lab/`). A árvore NÃO SHALL listar arquivos individuais dentro de qualquer subdiretório (profundidade 2 ou maior), incluindo `docs/`, `docs/adr/`, `scripts/` e qualquer caminho sob `src/`.

#### Scenario: Árvore lista apenas diretórios e arquivos de raiz
- **WHEN** o bloco de árvore em `README.md` contém apenas entradas de diretório (em qualquer profundidade) e entradas de arquivo restritas à raiz do projeto
- **THEN** a verificação de granularidade da árvore do README é aprovada sem erros

#### Scenario: Árvore lista um arquivo dentro de subdiretório
- **WHEN** o bloco de árvore em `README.md` contém uma entrada de arquivo em profundidade 2 ou maior (por exemplo, um arquivo `.py` listado individualmente sob `scripts/` ou `src/player_modeling/worker/`)
- **THEN** a verificação de granularidade da árvore do README reporta uma falha identificando a(s) linha(s) inválida(s)

### Requirement: Hook de pré-commit bloqueia violações da granularidade
O harness de desenvolvimento SHALL executar, antes de cada commit, uma verificação automatizada da granularidade da árvore de diretórios em `README.md`, bloqueando o commit (código de saída diferente de zero) quando o arquivo `README.md` está staged e sua árvore de diretórios viola a granularidade permitida.

#### Scenario: Commit com README.md staged violando a granularidade
- **WHEN** um commit é criado com `README.md` staged e sua árvore de diretórios lista um arquivo individual fora da raiz do projeto
- **THEN** o hook de pré-commit falha e o commit é bloqueado, exibindo mensagem indicando a(s) linha(s) e o motivo da violação

#### Scenario: Commit sem violação de granularidade
- **WHEN** um commit é criado e a árvore de diretórios em `README.md` (staged ou não) respeita a granularidade permitida, incluindo o caso em que `README.md` não foi alterado no commit
- **THEN** o hook de pré-commit é aprovado e não bloqueia o commit
