# ADR 0002 - GitFlow

* **Status:** Aceito
* **Data:** 2026-09-05
* **Decisão:** Definição das regras para commits, branches e pull requests.

## Contexto

O projeto é desenvolvido de forma incremental ao longo da disciplina PPGTI1101, com múltiplas tarefas sendo implementadas ao longo do tempo. É necessário definir um fluxo de branches e uma convenção de commits para manter o histórico organizado, rastreável e seguro, evitando que mudanças não testadas cheguem diretamente à branch principal.

## Decisão

### Estrutura de branches

O projeto utiliza três níveis de branch:

* `main`: branch de produção. Contém apenas código estável e validado. **Nunca recebe merge direto** de branches de tarefa.
* `dev`: branch de integração. Recebe o merge das branches de tarefa após estas terem sido testadas e validadas.
* branches de tarefa: uma branch por tarefa, criada a partir de `dev`.

Fluxo de merge:

```text
feature/tarefa-x ──► dev ──► main
```

Regras:

1. Toda tarefa (funcionalidade, correção, documentação, configuração, etc.) deve ser desenvolvida em sua própria branch.
2. Uma branch de tarefa só pode ser mergeada em `dev` após ter sido testada e validada (testes automatizados passando e revisão do desenvolvedor).
3. `main` só recebe merge a partir de `dev`, nunca diretamente de uma branch de tarefa.
4. Após o merge em `dev`, a branch de tarefa deve ser removida.

### Nomenclatura de branches

As branches de tarefa devem seguir o padrão:

```text
<tipo>/<descricao-curta>
```

Onde `<tipo>` indica a natureza da tarefa:

* `feature/`: nova funcionalidade;
* `fix/`: correção de bug;
* `refactor/`: refatoração sem mudança de comportamento;
* `docs/`: alterações de documentação (README, ADRs, etc.);
* `test/`: adição ou ajuste de testes;
* `chore/`: tarefas de manutenção, configuração ou infraestrutura do projeto.

`<descricao-curta>` deve estar em `kebab-case`, em português ou inglês (manter consistência com o restante do projeto), e descrever objetivamente o objetivo da tarefa.

Exemplos:

```text
feature/pipeline-ingestao-eventos
fix/validacao-eventos-invalidos
docs/adr-gitflow
chore/setup-ambiente-virtual
```

### Estrutura de commits

As mensagens de commit devem seguir o padrão:

```text
<PREFIXO>: <descrição objetiva>
```

Onde `<PREFIXO>` é escrito em maiúsculas e indica a natureza da alteração:

* `ADD`: adição de novo arquivo, funcionalidade ou dependência;
* `UPDATE`: alteração de código ou comportamento já existente;
* `FIX`: correção de bug;
* `REMOVE`: remoção de código, arquivo ou dependência;
* `REFACTOR`: refatoração sem mudança de comportamento externo;
* `DOCS`: alterações de documentação;
* `TEST`: adição ou ajuste de testes.

A descrição deve estar no imperativo, ser objetiva e refletir o que foi feito.

Exemplos (seguindo o histórico já utilizado no projeto):

```text
ADD: player events seed raw
ADD: mcp setup
ADD: adr e README.md
FIX: validação de eventos com timestamp inválido
```

## Consequências

* Reduz o risco de código não testado chegar à branch `main`.
* Facilita a rastreabilidade de cada tarefa através do nome da branch e das mensagens de commit.
* Exige disciplina para sempre abrir uma branch por tarefa e nunca commitar diretamente em `dev` ou `main`.
