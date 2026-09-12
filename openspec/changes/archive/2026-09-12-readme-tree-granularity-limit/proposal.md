## Why

A árvore de diretórios em `README.md` ("Estrutura do projeto") hoje lista manualmente cada arquivo folha de código e teste (ex.: cada `.py` em `scripts/`, `src/player_modeling/**` e `src/tests/**`). Isso não escala: à medida que o projeto cresce (dezenas ou centenas de arquivos), manter essa árvore sincronizada a cada novo arquivo se torna trabalho manual constante e sujeito a divergir da estrutura real. É necessário registrar essa decisão em ADR e adicionar um harness (hook de pré-commit) que bloqueie commits que voltem a listar arquivos individuais de subdiretórios de código/teste na árvore do README.md, permitindo apenas diretórios e arquivos de nível raiz do projeto.

## What Changes

- Adicionar ADR documentando a decisão de granularidade permitida na árvore de diretórios do `README.md`: a árvore pode listar diretórios (em qualquer profundidade) e arquivos que ficam diretamente na raiz do projeto (ex.: `CLAUDE.md`, `README.md`, `docker-compose.yml`, `Makefile`, `pyproject.toml`), mas não pode listar arquivos individuais dentro de subdiretórios (ex.: `scripts/*.py`, `docs/adr/*.md`, qualquer arquivo sob `src/**`).
- Reescrever a árvore de diretórios existente em `README.md` (seção "Estrutura do projeto") para respeitar essa regra, colapsando os subdiretórios de código/teste/ADR para não listarem arquivos individuais.
- Implementar um novo script de harness em `scripts/` que analisa o bloco de árvore ASCII em `README.md` e falha (código de saída != 0) se encontrar uma entrada de arquivo em profundidade maior que a raiz do projeto.
- Registrar o novo hook em `.pre-commit-config.yaml`, seguindo o padrão dos hooks locais existentes (ex.: `check-sensitive-paths`).
- Adicionar testes unitários do novo script em `src/tests/scripts/`, espelhando a convenção dos testes de harness existentes.
- Atualizar `CLAUDE.md`/README.md apenas quanto à documentação do comando de harness (nenhum aspecto de escopo funcional do produto é alterado).

Fora de escopo (ver seção "Não fazer" do `CLAUDE.md`): nenhuma mudança em simulador, worker, banco de dados, modelo de ML, endpoints da API, frontend, autenticação, CI/CD ou infraestrutura de produção. Esta change é puramente sobre convenção de documentação e harness de desenvolvimento.

## Capabilities

### New Capabilities
- `harness/readme-tree-granularity`: valida, via hook de pré-commit, que a árvore de diretórios do `README.md` não lista arquivos individuais fora da raiz do projeto.

### Modified Capabilities
(nenhuma - não há capacidade de spec existente sendo alterada; esta é a primeira spec do domínio de harness de documentação.)

## Impact

- Código afetado: novo módulo em `scripts/` (ex.: `scripts/check_readme_tree_granularity.py`) e testes correspondentes em `src/tests/scripts/`.
- Configuração: novo hook local em `.pre-commit-config.yaml`.
- Documentação: novo ADR em `docs/adr/`; edição do bloco de árvore em `README.md` (seção "Estrutura do projeto") para conformidade com a nova regra.
- Sem impacto em dependências externas, banco de dados, API ou pipeline de dados.
