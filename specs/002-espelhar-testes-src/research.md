# Phase 0 Research: Espelhar src/tests/ pela organização dos módulos verificados

Nenhum `[NEEDS CLARIFICATION]` foi deixado na spec. Este documento registra as decisões tomadas a partir da inspeção do repositório atual, não de pesquisa externa.

## Decisão 1: `conftest.py` permanece na raiz de `src/tests/`, não é duplicado em `src/tests/scripts/`

- **Decision**: Manter `src/tests/conftest.py` onde está; não criar `src/tests/scripts/conftest.py`.
- **Rationale**: O pytest descobre e aplica automaticamente qualquer `conftest.py` encontrado em um diretório ancestral de um teste — um `conftest.py` em `src/tests/` já se aplica a `src/tests/scripts/` sem nenhuma configuração adicional. Duplicá-lo criaria dois pontos de manutenção para a mesma responsabilidade (tornar `scripts/` importável).
- **Alternatives considered**: Mover `conftest.py` para `src/tests/scripts/` junto com os testes — rejeitado porque, se um teste futuro for adicionado fora de `src/tests/scripts/` (ex.: `src/tests/player_modeling/...`), ele também precisaria dos scripts de harness no `sys.path` ou de sua própria configuração; manter na raiz da suíte generaliza melhor.

## Decisão 2: Apenas os testes de harness são movidos; nenhuma estrutura é criada para `player_modeling/*`

- **Decision**: Criar somente `src/tests/scripts/`. Não criar `src/tests/player_modeling/{api,ml,simulator,worker,scripts}/`.
- **Rationale**: `CLAUDE.md` proíbe implementar/estruturar antecipadamente funcionalidades sem código de negócio associado. Como `src/player_modeling/{api,ml,simulator,worker}` ainda são apenas `__init__.py` placeholders e `src/player_modeling/scripts/generate_raw_events.py` nunca teve testes, criar diretórios de teste vazios para eles seria estrutura especulativa, não reorganização de algo existente.
- **Alternatives considered**: Criar a árvore completa de testes espelhando todo `src/player_modeling/` desde já, com diretórios vazios (ou com `__init__.py`) para uso futuro — rejeitado por violar a regra "não implementar funcionalidades futuras sem solicitação" e por não ter nenhum teste real para colocar neles agora.

## Decisão 3: Nenhuma mudança de import é necessária dentro dos testes movidos

- **Decision**: Os arquivos de teste movidos não precisam de nenhuma alteração de código (`import` continua igual: `from check_branch import ...`, etc.).
- **Rationale**: Os testes importam os módulos de harness pelo nome simples (não por caminho relativo ao próprio arquivo de teste), e essa resolução depende apenas do `sys.path` configurado pelo `conftest.py` (que permanece funcional, ver Decisão 1) — não da posição do arquivo de teste em si.
- **Alternatives considered**: N/A — verificado diretamente lendo o conteúdo de cada teste antes de mover.

## Decisão 4: Nenhuma configuração de `pyproject.toml` precisa mudar

- **Decision**: `testpaths = ["src/tests"]` (definido na feature 001) já cobre `src/tests/scripts/` recursivamente; nenhuma mudança adicional é necessária.
- **Rationale**: O pytest, por padrão, descobre testes recursivamente dentro de `testpaths`.
- **Alternatives considered**: N/A.
