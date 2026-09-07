# Feature Specification: Espelhar src/tests/ pela organização dos módulos verificados

**Feature Branch**: `002-espelhar-testes-src`

**Created**: 2026-09-06

**Status**: Draft

**Input**: User description: "Reorganizar a estrutura de src/tests/ para que reflita a organização dos módulos que cada teste verifica, conforme o item 5 de docs/escopo.md, complementando a reorganização do backend já feita no item 4 (feature 001-reorganizar-backend-src, onde tests/ foi movido para src/tests/). Regra: cada teste deve ficar no caminho correspondente ao módulo que verifica. Hoje src/tests/ contém, de forma plana, cinco testes que verificam scripts de harness localizados em scripts/ na raiz do projeto (test_block_git_push_hook.py, test_check_branch.py, test_check_commit_message.py, test_check_sensitive_paths.py, test_report_scope_diff.py) e um conftest.py compartilhado que torna esses scripts importáveis via sys.path. Esses cinco testes devem ser movidos para src/tests/scripts/, espelhando o diretório scripts/ que eles verificam (ex.: o teste de scripts/check_branch.py deve estar em src/tests/scripts/test_check_branch.py). O conftest.py compartilhado deve permanecer em src/tests/ (raiz da suíte), pois o pytest já propaga fixtures/configuração de um conftest.py para todos os subdiretórios, e ele deve continuar funcionando corretamente para os testes agora aninhados um nível mais fundo. O mesmo princípio de espelhamento deve ficar documentado como convenção para quando os módulos de domínio (src/player_modeling/api, ml, simulator, worker, scripts) ganharem testes no futuro — mas esta feature NÃO deve criar diretórios de teste vazios ou especulativos para módulos que ainda não têm código de negócio implementado. Critério de conclusão: a convenção de prefixo test_ é preservada, os imports/configuração do pytest continuam funcionando tanto localmente quanto na configuração de CI, a suíte completa (poetry run pytest) e os testes individuais continuam passando, os caminhos antigos não são mais necessários, e a documentação (CLAUDE.md/README.md) reflete a nova estrutura. Esta é uma reorganização estrutural que não deve alterar o comportamento nem a cobertura dos testes existentes."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Testes de harness espelham o diretório scripts/ que verificam (Priority: P1)

Como desenvolvedor(a) do projeto (ou agente de IA de desenvolvimento), preciso que os testes dos scripts de harness estejam organizados em `src/tests/scripts/`, no mesmo padrão de subdiretório do módulo `scripts/` que verificam, para localizar rapidamente o teste correspondente a um script e entender, pela estrutura de diretórios, a relação entre código e cobertura.

**Why this priority**: É o núcleo do item 5 do escopo — hoje todos os testes existentes estão soltos em `src/tests/`, sem nenhuma relação estrutural explícita com o que verificam; esta é a única mudança necessária dado o estado atual do repositório (não há testes para módulos de domínio ainda, pois não há código de negócio implementado).

**Independent Test**: Pode ser validado revisando a árvore de `src/tests/` e confirmando que os cinco arquivos de teste de harness estão em `src/tests/scripts/`, e executando `poetry run pytest src/tests/scripts/test_check_branch.py` (e os demais) individualmente com sucesso.

**Acceptance Scenarios**:

1. **Given** os testes `test_block_git_push_hook.py`, `test_check_branch.py`, `test_check_commit_message.py`, `test_check_sensitive_paths.py` e `test_report_scope_diff.py`, hoje soltos em `src/tests/`, **When** a reorganização é aplicada, **Then** cada um passa a residir em `src/tests/scripts/`, mantendo o prefixo `test_` e o nome correspondente ao script que verifica (ex.: `src/tests/scripts/test_check_branch.py` testa `scripts/check_branch.py`).
2. **Given** os testes movidos para `src/tests/scripts/`, **When** `poetry run pytest` é executado a partir da raiz do projeto, **Then** todos os testes são descobertos e executados com sucesso, com o mesmo resultado (mesma quantidade de testes, nenhuma regressão) de antes da reorganização.
3. **Given** um teste individual movido, **When** ele é executado isoladamente (ex.: `poetry run pytest src/tests/scripts/test_check_sensitive_paths.py`), **Then** ele importa corretamente o script de harness correspondente e passa, sem erro de import.

---

### User Story 2 - Fixtures e configuração compartilhadas continuam funcionando após o espelhamento (Priority: P1)

Como desenvolvedor(a) mantendo a suíte de testes, preciso que o `conftest.py` compartilhado continue disponibilizando os scripts de harness para import (via `sys.path`) para todos os testes, mesmo depois de eles serem movidos um nível mais fundo na árvore de diretórios, para não duplicar essa configuração em cada subdiretório de teste.

**Why this priority**: Sem isso, a User Story 1 quebra: mover os testes sem garantir que a configuração compartilhada continue alcançando-os tornaria os testes de harness não executáveis (falha de import). É tão crítico quanto a US1 e deve ser entregue junto.

**Independent Test**: Pode ser validado executando a suíte completa (`poetry run pytest`) e confirmando que nenhum teste falha por `ModuleNotFoundError`, e inspecionando que `src/tests/conftest.py` permanece na raiz da suíte (não duplicado em `src/tests/scripts/`).

**Acceptance Scenarios**:

1. **Given** o `conftest.py` em `src/tests/` (raiz da suíte de testes), **When** os testes de harness são movidos para `src/tests/scripts/`, **Then** o `conftest.py` permanece em `src/tests/` (não é duplicado nem movido) e continua sendo aplicado automaticamente aos testes em `src/tests/scripts/`, por herança padrão do pytest.
2. **Given** a suíte de testes reorganizada, **When** `poetry run pytest` é executado, **Then** nenhum teste falha por erro de import dos scripts de harness (`ModuleNotFoundError` ou equivalente).

---

### User Story 3 - Convenção de espelhamento documentada para módulos futuros (Priority: P2)

Como desenvolvedor(a) que vai adicionar testes para os módulos de domínio (`api`, `ml`, `simulator`, `worker`, `scripts` de `src/player_modeling/`) conforme a pipeline for implementada, preciso que a convenção de espelhamento estrutural entre `src/player_modeling/` (e `scripts/`, na raiz) e `src/tests/` esteja documentada no `CLAUDE.md`, para saber onde colocar cada novo teste sem precisar deduzir a regra novamente.

**Why this priority**: Tem valor de prevenção de inconsistência futura, mas não bloqueia a reorganização dos testes existentes (US1/US2); pode ser entregue depois, como complemento textual.

**Independent Test**: Pode ser validado revisando a seção "Testes" do `CLAUDE.md` e confirmando que ela descreve a regra de espelhamento com um exemplo concreto do estado atual do repositório.

**Acceptance Scenarios**:

1. **Given** a seção "Testes" do `CLAUDE.md`, **When** a reorganização é concluída, **Then** ela explicita que cada teste deve ficar no caminho de `src/tests/` correspondente ao módulo que verifica (espelhando `scripts/` e, futuramente, `src/player_modeling/*`), com um exemplo real da estrutura atual (`src/tests/scripts/test_check_branch.py` para `scripts/check_branch.py`).
2. **Given** os módulos de domínio `src/player_modeling/{api,ml,simulator,worker,scripts}` que ainda não têm código de negócio implementado, **When** a reorganização é concluída, **Then** nenhum diretório de teste vazio ou especulativo é criado para eles — a convenção fica documentada, mas aplicada somente quando esses módulos ganharem código e testes reais.

---

### Edge Cases

- O que acontece se um novo teste for adicionado para `src/player_modeling/scripts/generate_raw_events.py` no futuro? Deve seguir a convenção documentada (ex.: `src/tests/player_modeling/scripts/test_generate_raw_events.py`), mas isso está fora do escopo desta feature (não cria testes novos).
- Como o sistema se comporta se um teste de harness for executado isoladamente por caminho completo (ex.: `poetry run pytest src/tests/scripts/test_report_scope_diff.py::test_alteracao_em_dado_bruto_e_sinalizada`)? Deve funcionar exatamente como antes da reorganização, apenas com o caminho atualizado.
- O que acontece com o cache de bytecode (`__pycache__`) dos testes no caminho antigo? Deve ser possível removê-lo sem afeitar a suíte, já que não é rastreado pelo Git (ver `.gitignore`).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A reorganização MUST mover os cinco testes de harness (`test_block_git_push_hook.py`, `test_check_branch.py`, `test_check_commit_message.py`, `test_check_sensitive_paths.py`, `test_report_scope_diff.py`) de `src/tests/` para `src/tests/scripts/`, preservando o prefixo `test_` e o nome de cada arquivo.
- **FR-002**: A reorganização MUST manter `src/tests/conftest.py` em `src/tests/` (raiz da suíte), sem duplicá-lo em `src/tests/scripts/`.
- **FR-003**: A reorganização MUST garantir que os scripts de harness (`scripts/*.py`, na raiz do projeto) continuem importáveis pelos testes movidos, sem alterar a lógica de disponibilização via `sys.path` além do necessário para funcionar a partir do novo caminho.
- **FR-004**: A reorganização MUST NOT criar diretórios ou arquivos de teste para módulos que ainda não têm código de negócio implementado (`src/player_modeling/{api,ml,simulator,worker,scripts}`).
- **FR-005**: A reorganização MUST NOT alterar o conteúdo lógico dos testes (asserts, casos de teste, fixtures) — apenas sua localização no sistema de arquivos.
- **FR-006**: A reorganização MUST atualizar toda referência a caminhos de teste afetados — documentação (`CLAUDE.md`, `README.md`), configuração de cobertura/CI, se existente — para os novos caminhos.
- **FR-007**: A reorganização MUST garantir que a suíte completa (`poetry run pytest`) e cada teste individual continuem passando após a mudança, com a mesma quantidade de testes coletados de antes.
- **FR-008**: A documentação final MUST descrever a convenção de espelhamento entre módulos e testes de forma genérica (aplicável a futuros módulos de `src/player_modeling/`), não apenas para o caso atual dos scripts de harness.

### Key Entities

- **Teste de harness**: Arquivo `test_*.py` que verifica um script específico de `scripts/` (raiz); passa a residir em `src/tests/scripts/`.
- **Configuração compartilhada (`conftest.py`)**: Arquivo de fixtures/configuração do pytest que permanece na raiz de `src/tests/`, aplicado por herança a todos os subdiretórios de teste.
- **Convenção de espelhamento**: Regra documentada que associa o caminho de um teste ao caminho do módulo que ele verifica, dentro de `src/tests/`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos testes de harness existentes residem em `src/tests/scripts/`, espelhando `scripts/`.
- **SC-002**: `poetry run pytest` continua coletando e aprovando o mesmo número de testes (46) de antes da reorganização.
- **SC-003**: Cada teste pode ser executado individualmente pelo novo caminho sem erro de import.
- **SC-004**: Zero diretórios de teste vazios ou especulativos são criados para módulos sem código de negócio implementado.
- **SC-005**: A seção "Testes" do `CLAUDE.md` descreve a convenção de espelhamento com um exemplo verificável no repositório.

## Assumptions

- Não há, no momento, testes para os módulos de domínio (`src/player_modeling/{api,ml,simulator,worker,scripts}`); portanto, esta feature reorganiza apenas os testes de harness existentes, sem criar estrutura especulativa para os demais módulos.
- `src/tests/conftest.py` é o único mecanismo de compartilhamento de configuração entre os testes atuais; o pytest propaga automaticamente um `conftest.py` de diretório pai para seus subdiretórios, dispensando duplicação.
- Não existe, hoje, configuração de cobertura de testes (`coverage`) que precise de ajuste de caminho; caso surja no futuro, deverá seguir a mesma convenção.
- Esta feature não introduz, remove nem altera comportamento de negócio nem cobertura de teste; é estritamente estrutural (reorganização de arquivos de teste e atualização de documentação).
