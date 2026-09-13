# Etapa 1 — Autonomia e guardrail na prática

## Tarefa escolhida

Criar `src/player_modeling/scripts/evaluate_model.py`: um script CLI que avalia o classificador
de personas sobre o dataset sintético rotulado e imprime acurácia e relatório por classe,
reaproveitando `evaluate_classifier()` de `src/player_modeling/ml/knn.py`.

Tarefa pequena, de baixo risco (somente leitura do dataset), com fronteira clara — adequada para
isolar a variável "modo de autonomia" do resto.

> **Transparência metodológica:** os dois modos foram **simulados dentro de uma mesma sessão**,
> não alternados no seletor da ferramenta (Shift+Tab). A execução A foi conduzida sob a restrição
> de plan mode (o agente só podia produzir plano, sem tocar em arquivo algum) e a execução B sob
> a restrição de auto-accept (o agente editava e executava sem pedir confirmação). Os tempos são
> reais, medidos com `date` no início e no fim de cada execução; a percepção de controle e risco
> é do desenvolvedor.

## Execução A — plan mode (simulado)

| | |
|---|---|
| Início / fim | 11:08:31 → 11:08:47 |
| Tempo | **~16 s** |
| Arquivos alterados | **nenhum** (`git status --short` vazio) |
| Saída produzida | um plano textual: arquivo a criar, função a reaproveitar, argumentos do `argparse`, tratamento de erro, alvo de `Makefile`, docs a atualizar, e a nota "não altera `src/data/*.csv`" |

O plano foi legível em uma tela e deixou explícito o ponto que mais importava revisar: **qual
função seria reaproveitada**. Se o agente tivesse proposto reimplementar `train_test_split` +
métricas dentro do script (duplicando `evaluate_classifier`), isso teria sido visível antes de
qualquer linha ser escrita.

## Execução B — auto-accept edits (simulado)

| | |
|---|---|
| Início / fim | 11:08:53 → 11:09:14 |
| Tempo | **~21 s** (13 s até o arquivo escrito, +7 s para rodar e validar a saída) |
| Arquivos alterados | 1 novo (`src/player_modeling/scripts/evaluate_model.py`, 97 linhas) |
| Verificação | script executado de fato: acurácia 0.9433 sobre 300 amostras de teste |

O código nasceu já validado por execução real — o que o plan mode não entrega. Em compensação,
a revisão humana passou a ser feita **sobre 97 linhas prontas**, não sobre 12 linhas de plano.

## Comparação

| Critério | Plan mode | Auto-accept edits |
|---|---|---|
| Tempo até o artefato | 16 s (plano) | 21 s (código rodando) |
| Tempo total incluindo revisão | maior — o plano ainda precisa virar código em uma segunda rodada | menor para tarefa pequena |
| Superfície de revisão | 12 linhas de intenção | 97 linhas de implementação |
| Momento de detectar erro de abordagem | **antes** de escrever | **depois**, lendo o diff |
| Sensação de controle | alta — nada acontece sem aprovação explícita | média — o controle existe, mas é *a posteriori*, via `git diff` |
| Risco percebido | baixo; o custo de um plano ruim é descartá-lo | proporcional ao **alcance** da tarefa, não ao seu tamanho: mesma tarefa seria muito mais arriscada se tocasse `src/data/` ou uma migração |
| Onde cada modo se paga | tarefas com decisão de arquitetura, dependência nova, mudança de contrato | tarefas aditivas, isoladas e reversíveis por `git checkout` |

## O que a comparação revelou

**1. Para tarefas pequenas e aditivas, o plan mode custa mais do que protege.** A diferença de
tempo bruto foi de 5 segundos, mas o plan mode exige *duas* rodadas (planejar, depois executar)
enquanto o auto-accept entrega em uma. Num arquivo novo, sem dependência e sem contrato
alterado, o `git diff` já é um mecanismo de revisão suficiente — o plano adiciona cerimônia sem
adicionar segurança.

**2. O que decide o modo não é o tamanho da tarefa, é o que ela alcança.** A mesma tarefa de
~90 linhas seria uma escolha ruim para auto-accept se tocasse `src/data/*.csv` (dataset de
treino), uma migração Alembic ou o contrato de um endpoint. O critério útil não é "quantas
linhas" mas "o que é irreversível ou invisível se sair errado" — e é exatamente aí que entra o
guardrail da próxima seção.

**3. Modo de autonomia e guardrail resolvem problemas diferentes e não se substituem.** O plan
mode depende de o humano **ler** o plano e perceber o problema; o hook não depende de ninguém
perceber nada. Durante esta atividade, o hook bloqueou uma escrita que o próprio agente tentou
fazer sem ter percebido que era proibida (seção 7 de `etapa1-evidencia-hook.md`) — o plan mode
não teria evitado isso, porque a ação nem sequer aparecia no plano.

## Guardrail configurado (tarefas 3 e 4)

Hook `PreToolUse` **`scripts/block_raw_data_write_hook.py`**, risco escolhido: **corrupção
silenciosa do dataset de origem** (`src/data/events.csv`, `src/data/sessions_features.csv`).

Por que esse risco, e não "bloquear merge na main":

* é um risco **deste** projeto — esses CSVs são a fonte de verdade que pré-treina o classificador
  de personas (ADR 0010) e a regra "Não modificar dados brutos" do `CLAUDE.md` era, até aqui,
  apenas texto;
* a falha é **silenciosa**: alterar o dataset muda o modelo servido pela API e **nenhum teste
  falha** — os testes de `ml/knn.py` verificam limiares de acurácia, não a integridade do dataset;
* os controles existentes chegam tarde demais: `report_scope_diff.py` é informativo e roda depois,
  e o pre-commit só age no commit. O `PreToolUse` é o único ponto do harness que age **antes**.

O que bloqueia: `Write`, `Edit`, `NotebookEdit` com `file_path` protegido, e `Bash` com
redirecionamento (`>`, `>>`) ou utilitário de escrita/remoção (`rm`, `mv`, `cp`, `tee`,
`truncate`, `dd`, `sed`) sobre um caminho protegido — inclusive em formas equivalentes (`./`,
`..`, caminho absoluto).

O que continua livre: toda leitura (`cat`, `head`, `grep`, `wc`, `pandas.read_csv`) e o caminho
sancionado de regeneração (`generate_raw_events.py`).

Evidência do bloqueio funcionando, incluindo tentativas reais do agente na sessão:
[`etapa1-evidencia-hook.md`](etapa1-evidencia-hook.md).
