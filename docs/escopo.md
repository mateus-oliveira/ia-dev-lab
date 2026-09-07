# Escopo das próximas funcionalidades

## Objetivo

Antes de implementar a pipeline de Player Modeling dentro de `src/`, será estruturada uma base de regras e mecanismos de controle para tornar o desenvolvimento incremental, rastreável e seguro. Esta etapa não implementará funcionalidades de negócio da pipeline; ela preparará o projeto para que as próximas alterações sigam padrões verificáveis. Para tal, serão testadas as ferramenteas de SDD *OpenSpec* e *Github Spec Kit*.

## 1. Definição das regras gerais de desenvolvimento

As regras gerais serão documentadas no `CLAUDE.md` e, quando representarem decisões arquiteturais ou processuais relevantes, em novos Architecture Decision Records (ADRs). O objetivo é reduzir ambiguidades nas contribuições humanas e nas alterações produzidas por ferramentas de IA.

### Python

Serão definidos, no mínimo:

* uso de Python 3.13 e de type hints nas interfaces públicas;
* nomenclatura em `snake_case` para funções e variáveis, `PascalCase` para classes e `UPPER_CASE` para constantes;
* docstrings para módulos, classes e funções públicas, com descrição dos parâmetros, retorno e exceções relevantes;
* separação de responsabilidades por domínio, evitando concentrar ingestão, transformação e geração de features no mesmo módulo;
* tratamento explícito de erros de validação, sem ocultar falhas de dados de entrada;
* preferência por funções pequenas, testáveis e sem efeitos colaterais desnecessários;
* testes unitários para transformações, validações e regras de geração de features;
* formatação e lint consistentes, executados automaticamente pelo harness.

### TypeScript

Caso o projeto passe a incluir código TypeScript, serão definidos, no mínimo:

* interfaces, tipos e enums compartilhados em módulos `.ts` próprios, em vez de serem declarados dentro de arquivos `.tsx` sem necessidade;
* nomenclatura consistente para tipos, componentes, funções e constantes;
* separação entre componentes de apresentação, regras de negócio e acesso a dados;
* tipagem explícita nas fronteiras entre módulos e prevenção do uso indiscriminado de `any`;
* testes e verificação de tipos executados antes da integração das alterações;
* configuração única de formatação, lint e compilação para evitar divergência entre editores e contribuintes.

### Regras de documentação e arquitetura

Também serão estabelecidos:

* critérios para decidir quando uma mudança deve gerar ou atualizar um ADR;
* convenções para nomes de arquivos, diretórios, testes e scripts;
* obrigação de manter dados brutos em `data/raw/` sem sobrescrevê-los;
* atualização do `README.md` e do `CLAUDE.md` quando comandos, estrutura ou fluxo de desenvolvimento forem alterados;
* registro das limitações e das decisões tomadas com apoio de IA, preservando a revisão humana prevista na ADR 0001.

## 2. Configuração do harness do projeto

O harness será o conjunto de configurações, hooks, scripts e verificações que orientará o ciclo de desenvolvimento. Ele deve impedir ou sinalizar comportamentos indesejados sem substituir a decisão do desenvolvedor.

### Controles imprescindíveis

* **Proteção de branches:** configurar o repositório para impedir pushes diretos em `main` e `dev`, exigindo Pull Request e verificações aprovadas. Isso reforça o fluxo definido na ADR 0002.
* **Validação da branch atual:** criar um comando de verificação que confirme se a tarefa está sendo executada em uma branch compatível com o tipo de alteração. O harness deve alertar ou bloquear operações perigosas em `main` e `dev`.
* **Hooks de pré-commit:** executar formatação, lint, verificação de tipos quando aplicável e testes rápidos antes do commit. O hook deve apenas validar e nunca criar commits automaticamente.
* **Verificação de mensagens de commit:** conferir o padrão de prefixos definido na ADR 0002, mantendo o histórico rastreável.
* **CI em Pull Requests:** repetir as verificações em ambiente limpo, pois hooks locais podem ser ignorados ou não estar instalados. Nenhum merge deve ocorrer com validações obrigatórias falhando.
* **Bloqueio de commits automáticos por ferramentas de IA:** documentar explicitamente que agentes podem propor alterações, mas não podem executar `git commit`, `git push`, merge ou alteração de branch sem autorização explícita. A revisão humana deve ocorrer antes dessas operações.
* **Detecção de alterações fora do escopo:** informar arquivos modificados e diferença em relação à branch de origem antes de concluir uma tarefa, reduzindo o risco de alterações acidentais em dados brutos, configurações ou outros módulos.
* **Validação de arquivos sensíveis:** impedir o versionamento de segredos, credenciais, ambientes virtuais, artefatos de execução e dados pessoais. Os eventos usados no projeto devem continuar sintéticos.
* **Reprodutibilidade do ambiente:** centralizar versões, dependências e comandos de validação para que a execução local e a CI produzam resultados comparáveis.

### Limites do harness

O harness deve bloquear operações objetivamente perigosas, como commit automático, push direto em branches protegidas e inclusão de segredos. Para decisões que exigem contexto, como a qualidade de uma regra de negócio, ele deve produzir uma falha clara ou um alerta para revisão, sem tentar substituir o julgamento humano.

Os controles serão implementados gradualmente, começando por scripts de validação e hooks locais, seguidos pela configuração de CI e pela proteção das branches no repositório remoto. Cada controle deverá possuir documentação e, quando aplicável, um teste que demonstre seu comportamento.

## 3. Uso de SDD antes da implementação da pipeline

Será utilizado **SDD (Specification-Driven Development)** para especificar, revisar e validar essas funcionalidades antes de escrever o código da pipeline em `src/`. A especificação servirá como contrato para as regras de Python, TypeScript e para o harness, tornando explícitos os comportamentos esperados, os critérios de aceitação e os limites de cada controle.

Essa abordagem é importante neste projeto porque as primeiras decisões são principalmente de processo, arquitetura e governança. Codificar a pipeline antes de definir essas regras poderia gerar módulos inconsistentes, testes incompletos e retrabalho quando o harness fosse introduzido. Com SDD, cada funcionalidade poderá ser decomposta em uma especificação verificável, implementada de forma incremental e validada por testes ou checks automatizados antes de ser considerada concluída.

O SDD também cria uma referência comum para o desenvolvedor e para as ferramentas de IA. Isso facilita a revisão humana, reduz interpretações divergentes dos prompts e mantém a implementação alinhada às ADRs. Depois que as regras e os critérios de aceitação estiverem definidos, a implementação em `src/` poderá concentrar-se no comportamento da pipeline, sem precisar resolver simultaneamente convenções básicas e controles do fluxo de trabalho.

## 4. Reorganização dos artefatos do backend

O projeto será reorganizado para que os diretórios e arquivos relacionados exclusivamente à implementação do backend fiquem agrupados dentro de `src/`. Essa mudança será especificada e implementada com o GitHub Spec Kit, preservando o comportamento atual e evitando alterações desnecessárias na organização dos artefatos de governança do projeto.

Como parte dessa reorganização, deverão ser avaliados, no mínimo:

* mover o código de domínio atualmente distribuído em `src/player_modeling/` para uma estrutura interna coerente, mantendo separados os módulos de API, modelo de ML, simulador e worker;
* mover scripts executáveis que façam parte do backend ou da operação da pipeline para uma área própria sob `src/`, distinguindo-os de ferramentas de desenvolvimento e validação do harness;
* avaliar a localização dos dados usados pela aplicação, mantendo dados brutos e artefatos de entrada separados do código e sem sobrescrevê-los durante a execução;
* identificar outros arquivos de implementação que estejam fora de `src/` e realocá-los quando a mudança preservar suas responsabilidades e facilitar a manutenção;
* manter na raiz os arquivos de configuração e documentação do projeto, como `pyproject.toml`, `poetry.toml`, `README.md`, `CLAUDE.md` e `docs/`, salvo justificativa documentada para uma alteração;
* atualizar imports, comandos, configurações, documentação e referências afetados pela nova estrutura;
* garantir que a reorganização não misture código de produção com arquivos temporários, ambientes virtuais, dados sensíveis ou artefatos gerados.

A funcionalidade será considerada concluída quando a estrutura resultante estiver documentada, os comandos de desenvolvimento continuarem reproduzíveis e os testes existentes passarem sem depender dos caminhos antigos.

## 5. Organização dos testes por espelhamento do código

A estrutura de `tests/` deverá refletir a organização dos módulos de implementação em `src/`, facilitando a localização dos testes e tornando explícita a relação entre código e cobertura. Essa mudança também será especificada e implementada com o GitHub Spec Kit.

Como regra, cada teste deverá ficar no caminho correspondente ao módulo que verifica. Por exemplo, o teste de `src/scripts/block_git_push_hook.py` deverá estar em `tests/scripts/test_block_git_push_hook.py`. O mesmo princípio deverá ser aplicado aos módulos de API, modelo de ML, simulador, worker e demais áreas que venham a ser criadas.

A reorganização deverá:

* preservar a convenção de prefixar arquivos de teste com `test_`;
* manter testes unitários próximos, por estrutura de diretórios, ao código sob teste, sem copiar arquivos de produção para `tests/`;
* atualizar imports, configurações do pytest, cobertura, comandos do harness e documentação que dependam dos caminhos atuais;
* manter fixtures e utilitários compartilhados em uma localização claramente definida, sem quebrar o espelhamento dos testes específicos de cada módulo;
* garantir que a execução da suíte completa e dos testes individuais funcione tanto localmente quanto na CI.

A funcionalidade será considerada concluída quando todos os testes estiverem em diretórios compatíveis com os módulos correspondentes, os caminhos antigos não forem mais necessários e a suíte automatizada continuar passando.
