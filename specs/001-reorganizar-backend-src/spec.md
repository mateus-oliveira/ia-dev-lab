# Feature Specification: Reorganizar artefatos do backend sob src/

**Feature Branch**: `001-reorganizar-backend-src`

**Created**: 2026-09-06

**Status**: Draft

**Input**: User description: "Reorganizar os artefatos do backend para que fiquem agrupados dentro de src/, conforme o item 4 de docs/escopo.md: mover o código de domínio hoje em src/player_modeling/ para uma estrutura interna coerente mantendo separados os módulos de API, modelo de ML, simulador e worker; mover scripts executáveis do backend/pipeline para uma área própria sob src/, distinguindo-os de ferramentas de desenvolvimento/harness; avaliar a localização dos dados usados pela aplicação, mantendo dados brutos e artefatos de entrada separados do código e sem sobrescrevê-los; identificar e realocar outros arquivos de implementação que estejam fora de src/ quando isso preservar responsabilidades e facilitar manutenção; manter na raiz os arquivos de configuração e documentação do projeto (pyproject.toml, poetry.toml, README.md, CLAUDE.md, docs/), salvo justificativa documentada; atualizar imports, comandos, configurações, documentação e referências afetadas pela nova estrutura; garantir que a reorganização não misture código de produção com arquivos temporários, ambientes virtuais, dados sensíveis ou artefatos gerados. Critério de conclusão: estrutura documentada, comandos de desenvolvimento reproduzíveis e testes existentes passando sem depender dos caminhos antigos. Esta é uma reorganização estrutural que deve preservar o comportamento atual, sem alterar regras de negócio."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scripts do backend/pipeline agrupados sob src/ (Priority: P1)

Como desenvolvedor(a) do projeto (ou agente de IA de desenvolvimento), preciso que os scripts executáveis que fazem parte da operação do backend/pipeline (por exemplo, a geração do dataset sintético usado para pré-treinar o modelo de ML) estejam localizados sob `src/`, separados dos scripts de harness (validação de branch, commit, arquivos sensíveis, diff de escopo), para que fique claro o que é código de produção da pipeline e o que é ferramenta de desenvolvimento do repositório.

**Why this priority**: É a mudança estrutural com maior impacto imediato: hoje um script de pipeline (`scripts/generate_raw_events.py`) está misturado com scripts de harness no mesmo diretório `scripts/`, dificultando a distinção entre "código do produto" e "ferramentas do repositório".

**Independent Test**: Pode ser validado de forma isolada executando o comando de geração do dataset a partir do novo caminho sob `src/` e confirmando que `src/data/events.csv` e `src/data/sessions_features.csv` são gerados corretamente, sem depender das demais mudanças desta feature.

**Acceptance Scenarios**:

1. **Given** o script de geração do dataset sintético hoje em `scripts/generate_raw_events.py`, **When** a reorganização é aplicada, **Then** o script passa a residir em uma área própria sob `src/` (ex.: `src/player_modeling/scripts/`), com nome e comportamento preservados.
2. **Given** o novo caminho do script sob `src/`, **When** o comando documentado no `CLAUDE.md`/`README.md` é executado, **Then** o dataset sintético é gerado corretamente em `src/data/`, com o mesmo formato de antes da reorganização.
3. **Given** os scripts de harness (`block_git_push_hook.py`, `check_branch.py`, `check_commit_message.py`, `check_sensitive_paths.py`, `report_scope_diff.py`), **When** a reorganização é concluída, **Then** eles permanecem fora de `src/`, em uma área claramente identificada como ferramentas de desenvolvimento/harness (não pipeline).

---

### User Story 2 - Estrutura de domínio coerente e documentada (Priority: P2)

Como desenvolvedor(a) que vai implementar a pipeline de Player Modeling em seguida, preciso que a estrutura interna de `src/player_modeling/` (módulos de API, modelo de ML, simulador e worker) esteja organizada e documentada de forma coerente, para que a futura implementação de cada módulo tenha um local óbvio e sem necessidade de nova reestruturação.

**Why this priority**: Prepara o terreno para a implementação de negócio (fora do escopo desta feature), evitando retrabalho estrutural quando o código de domínio for escrito.

**Independent Test**: Pode ser validado revisando a árvore de diretórios de `src/player_modeling/` e a documentação (`CLAUDE.md`/`README.md`), confirmando que a separação por domínio (api, ml, simulator, worker) está preservada e descrita, mesmo sem nenhum código de negócio ainda implementado.

**Acceptance Scenarios**:

1. **Given** a estrutura atual com os diretórios `src/player_modeling/{api,ml,simulator,worker}` vazios, **When** a reorganização é concluída, **Then** essa separação por domínio é preservada (ou justificadamente ajustada) e cada diretório contém um marcador versionável (ex.: `__init__.py`) que documenta seu propósito.
2. **Given** a documentação do projeto, **When** a reorganização é concluída, **Then** o `CLAUDE.md` (e o `README.md`, se aplicável) descreve a estrutura final de `src/` de forma consistente com o que existe no repositório.

---

### User Story 3 - Dados e testes agrupados sob src/, sem misturar com o código de domínio (Priority: P3)

Como desenvolvedor(a) responsável pela integridade do dataset sintético e da suíte de testes, preciso que `data/` e `tests/` passem a residir dentro de `src/` — já que `src/` passa a agrupar tudo o que é relacionado à implementação do backend — mas como diretórios irmãos de `src/player_modeling/`, não aninhados dentro do pacote de domínio. Os dados não podem ser sobrescritos nem ter seu conteúdo alterado como efeito colateral da reorganização.

**Why this priority**: Depende da conclusão de US1 (novo local do script gerador) para que a documentação e os comandos fiquem consistentes; é um critério explícito do item 4 do escopo (localização dos dados) e uma decisão de estrutura confirmada com o desenvolvedor durante a implementação.

**Independent Test**: Pode ser validado conferindo que `src/data/events.csv` e `src/data/sessions_features.csv` existem no novo caminho, que `data/` não existe mais na raiz, e que a suíte de testes (agora em `src/tests/`) continua passando com `poetry run pytest`.

**Acceptance Scenarios**:

1. **Given** os arquivos `data/events.csv` e `data/sessions_features.csv` na raiz do projeto, **When** a reorganização é aplicada, **Then** esses arquivos passam a residir em `src/data/` (não em `src/player_modeling/`), sem alteração de formato ou de finalidade.
2. **Given** o diretório `tests/` na raiz do projeto, **When** a reorganização é aplicada, **Then** ele passa a residir em `src/tests/` (não em `src/player_modeling/`), e `poetry run pytest` continua funcionando (via `testpaths` atualizado em `pyproject.toml`).
3. **Given** a documentação que descreve a origem dos dados, **When** a reorganização é concluída, **Then** o `CLAUDE.md` explicita que `src/data/events.csv` e `src/data/sessions_features.csv` são gerados exclusivamente por `src/player_modeling/scripts/generate_raw_events.py` e não devem ser editados manualmente.

---

### Edge Cases

- O que acontece com scripts de harness que hoje ficam no mesmo diretório (`scripts/`) do script de pipeline? Devem continuar funcionando a partir de seus caminhos atuais, sem depender de nada movido para `src/`.
- Como o sistema se comporta se algum comando documentado (`CLAUDE.md`, `README.md`, hooks de pré-commit, CI) ainda referenciar o caminho antigo do script de pipeline após a mudança? Deve ser tratado como falha de reorganização incompleta — todas as referências devem ser atualizadas.
- O que acontece com os diretórios vazios de `src/player_modeling/{api,ml,simulator,worker}` que hoje não são rastreados pelo Git (diretórios vazios não são versionados)? Devem passar a ser rastreáveis (ex.: via `__init__.py`) para que a estrutura fique explícita no repositório, sem exigir a criação prematura de código de negócio.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A reorganização MUST manter o código de domínio (`src/player_modeling/api`, `ml`, `simulator`, `worker`) separado por módulo, preservando a responsabilidade de cada um, sem introduzir código de negócio novo.
- **FR-002**: A reorganização MUST mover o(s) script(s) executável(is) que fazem parte da operação do backend/pipeline (atualmente `scripts/generate_raw_events.py`) para uma área própria sob `src/`, distinta dos scripts de harness.
- **FR-003**: A reorganização MUST manter os scripts de harness/validação de desenvolvimento (`block_git_push_hook.py`, `check_branch.py`, `check_commit_message.py`, `check_sensitive_paths.py`, `report_scope_diff.py`) fora de `src/`, em um diretório claramente identificado como ferramentas de desenvolvimento.
- **FR-004**: A reorganização MUST mover o diretório `data/` (com `events.csv` e `sessions_features.csv`) para `src/data/`, como irmão de `src/player_modeling/` (não aninhado dentro dele), sem alterar seu formato ou finalidade.
- **FR-004a**: A reorganização MUST mover o diretório `tests/` para `src/tests/`, como irmão de `src/player_modeling/`, atualizando `pyproject.toml` (`testpaths`) e qualquer referência de caminho relativo interna aos testes (ex.: `conftest.py`).
- **FR-005**: A reorganização MUST manter na raiz do projeto os arquivos de configuração e documentação (`pyproject.toml`, `poetry.toml`, `README.md`, `CLAUDE.md`, `docs/`), salvo justificativa documentada em contrário.
- **FR-006**: A reorganização MUST atualizar todas as referências a caminhos afetados — imports Python, comandos documentados em `CLAUDE.md`/`README.md`, configuração de ferramentas (`pyproject.toml`, `mypy_path`, hooks de pré-commit, CI) — para os novos caminhos.
- **FR-007**: A reorganização MUST preservar o comportamento observável dos comandos existentes (ex.: geração do dataset sintético) — mesmos argumentos, mesma saída — sem alterar regras de negócio.
- **FR-008**: A reorganização MUST garantir que a suíte de testes existente (`poetry run pytest`) continue passando após a mudança, sem depender de caminhos antigos.
- **FR-009**: A reorganização MUST NOT misturar código de produção com arquivos temporários, ambientes virtuais (`.venv`), dados sensíveis ou artefatos gerados (ex.: `__pycache__`, caches de ferramentas).
- **FR-010**: A estrutura final MUST estar documentada no `CLAUDE.md` (e no `README.md`, quando aplicável), refletindo fielmente os diretórios existentes no repositório.

### Key Entities

- **Módulo de domínio (`src/player_modeling/*`)**: Agrupamento de código por responsabilidade (api, ml, simulator, worker); ainda sem implementação de negócio, apenas estrutura.
- **Script de pipeline**: Script executável que participa da operação do backend/pipeline (ex.: geração do dataset sintético), a ser hospedado sob `src/`.
- **Script de harness**: Script executável usado para validar o processo de desenvolvimento (branch, commit, arquivos sensíveis, diff de escopo), que permanece fora de `src/`.
- **Dataset sintético (`src/data/*.csv`)**: Artefatos de dados de origem, gerados pelo script de pipeline, não editáveis manualmente e não sobrescritos pela reorganização.
- **Suíte de testes (`src/tests/`)**: Testes automatizados do projeto, movidos para dentro de `src/` como irmãos de `player_modeling/`; sua reorganização interna (espelhamento por módulo) é objeto do item 5 do escopo, não desta feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos scripts que operam a pipeline/backend estão localizados sob `src/`, e 100% dos scripts de harness permanecem fora de `src/`.
- **SC-002**: Todos os comandos de desenvolvimento documentados no `CLAUDE.md` (instalar dependências, rodar testes, gerar dataset, checagens do harness) continuam sendo executáveis com sucesso após a reorganização, sem alterações de comportamento.
- **SC-003**: 100% dos testes automatizados existentes (`poetry run pytest`) passam após a reorganização, sem referenciar caminhos antigos.
- **SC-004**: 100% dos arquivos de dados brutos (`src/data/events.csv`, `src/data/sessions_features.csv`) e da suíte de testes residem sob `src/` ao final da reorganização, sem alteração de formato ou de finalidade.
- **SC-005**: A documentação (`CLAUDE.md`) reflete a estrutura final de diretórios sem divergências identificáveis em revisão manual.

## Assumptions

- Não há, no momento, código de negócio implementado dentro de `src/player_modeling/{api,ml,simulator,worker}` (diretórios vazios); portanto, esta feature reorganiza apenas scripts, estrutura de diretórios e documentação, sem migrar lógica de negócio.
- O único script identificado como pertencente à operação do backend/pipeline, fora de `src/`, é `scripts/generate_raw_events.py`; os demais scripts em `scripts/` são ferramentas de harness e permanecem onde estão.
- `data/` e `tests/` movem-se para dentro de `src/` (como irmãos de `player_modeling/`), pois `src/` passa a agrupar tudo o que é relacionado à implementação do backend — decisão confirmada com o desenvolvedor durante a implementação, revisando a suposição inicial de manter esses diretórios na raiz.
- A reorganização interna de `tests/` (espelhamento por módulo, conforme item 5 do escopo) é tratada por uma feature separada (`002-*`); esta feature apenas relocaliza o diretório para `src/tests/`, preservando sua estrutura interna atual.
- Os arquivos de configuração e documentação de raiz (`pyproject.toml`, `poetry.toml`, `README.md`, `CLAUDE.md`, `docs/`) não serão movidos.
- Esta feature não introduz, remove nem altera comportamento de negócio; é estritamente estrutural (reorganização de arquivos, atualização de referências e documentação).
