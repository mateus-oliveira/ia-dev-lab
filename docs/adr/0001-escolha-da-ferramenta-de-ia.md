# ADR 0001 — Escolha da Ferramenta de IA para Desenvolvimento

* **Status:** Aceito
* **Data:** 2026-08-27
* **Decisão:** Utilizar Claude Code como ferramenta de desenvolvimento assistido por IA

## Contexto

O projeto **Player Modeling Lab** será desenvolvido no contexto da disciplina **PPGTI1101**.

A disciplina propõe a utilização prática de ferramentas de Inteligência Artificial durante o desenvolvimento de software, incluindo a organização do contexto do projeto, criação de prompts, integração com Git/GitHub e utilização de servidores MCP.

Para o desenvolvimento do projeto, é necessário selecionar uma ferramenta de IA que permita trabalhar de forma integrada ao código-fonte e ao contexto do repositório.

## Decisão

Foi escolhida a utilização do **Claude Code** como ferramenta principal de desenvolvimento assistido por IA neste projeto.

A ferramenta será utilizada como agente de apoio ao desenvolvimento, podendo auxiliar em atividades como:

* criação e modificação de código;
* análise da estrutura do projeto;
* criação de testes;
* refatoração;
* documentação;
* análise de problemas;
* execução de tarefas no repositório;
* interação com ferramentas disponibilizadas por MCP.

O arquivo `CLAUDE.md` será utilizado para fornecer à ferramenta o contexto permanente do projeto, incluindo objetivos, comandos, convenções de código e restrições.

## Justificativa

A escolha está relacionada principalmente à possibilidade de trabalhar com um agente de desenvolvimento orientado ao contexto do repositório.

O projeto possui uma estrutura que deverá evoluir ao longo da disciplina. Portanto, é importante que a ferramenta consiga considerar:

* a estrutura dos diretórios;
* as decisões arquiteturais;
* as convenções de código;
* os testes existentes;
* as regras específicas do projeto;
* as decisões registradas nos ADRs.

A utilização do `CLAUDE.md` permite centralizar essas informações e estabelecer um contexto consistente para as interações com a IA.

Além disso, a escolha está alinhada ao objetivo da disciplina de experimentar o desenvolvimento de software utilizando IA e avaliar, na prática, como o contexto fornecido à ferramenta influencia a qualidade das tarefas realizadas.

## Consequências

### Positivas

* O desenvolvimento passa a utilizar uma ferramenta de IA integrada ao contexto do projeto.
* O `CLAUDE.md` fornece um conjunto de regras persistentes para as interações.
* A ferramenta pode auxiliar em tarefas que envolvem múltiplos arquivos.
* O projeto poderá explorar posteriormente integração com MCP.
* A escolha fornece um caso concreto para avaliar diferentes estratégias de prompting.

### Negativas

* O código gerado pela IA pode conter erros e precisa de revisão humana.
* A qualidade das respostas depende da qualidade do contexto e dos prompts fornecidos.
* O uso excessivo da IA pode levar à implementação de soluções desnecessariamente complexas.
* A ferramenta escolhida não deve ser considerada autoridade sobre decisões arquiteturais ou científicas do projeto.

## Princípio de revisão humana

A utilização de IA não substitui a responsabilidade do desenvolvedor.

Alterações significativas devem ser revisadas antes de serem incorporadas ao projeto.

Quando a IA sugerir uma decisão arquitetural, o desenvolvedor deve avaliar os impactos e, quando necessário, registrar a decisão em um novo ADR.

## Relação com a disciplina

Esta decisão também servirá como base para as próximas atividades da disciplina, especialmente experimentos relacionados a:

* qualidade de prompts;
* desenvolvimento assistido por IA;
* Git/GitHub;
* Pull Requests;
* MCP;
* revisão humana de código gerado por IA.
