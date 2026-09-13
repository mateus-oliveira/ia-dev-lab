# Etapa 3 — Observabilidade e checkpoint humano

## Log da sessão (tarefa 8)

O transcript completo da sessão do agente está em [`docs/sessao-log.md`](../sessao-log.md),
exportado do JSONL bruto que o Claude Code mantém em
`~/.claude/projects/-Users-mateus-ufrn-mestrado-ia-dev-lab/`. Nada foi limpo ou editado: entradas de
ferramenta e resultados aparecem truncados apenas para manter o arquivo navegável, e o JSONL
original permanece intacto na máquina do desenvolvedor.

Vale registrar como o log foi obtido, porque é observabilidade sobre o próprio agente: o agente
**não conseguiu** ler o próprio transcript. A tentativa foi barrada pelo classificador do modo
automático do Claude Code, com o motivo `[Sensitive-Source Provenance]` — o diretório `~/.claude/`
é tratado como fonte sensível. O agente escreveu o exportador, e o desenvolvedor executou o comando.
Outro caso, como os das Etapas 1 e 2, em que o controle real só aparece quando é acionado.

## Checkpoint humano definido (tarefa 9)

> **Nenhuma alteração no contrato de resposta de um endpoint público é implementada sem aprovação
> explícita do desenvolvedor.** O agente para antes de escrever código, apresenta as formas possíveis
> do contrato com os trade-offs de cada uma, e espera a decisão.

### Por que este checkpoint, e não outro

A atividade sugere exemplos (antes de aplicar uma migração, antes de expor um endpoint, antes do
merge). Neste projeto, o contrato de resposta é o ponto certo:

* o projeto **já tem** controles técnicos para os outros riscos citados — `git push` é bloqueado por
  hook, commits em `main`/`dev` são bloqueados por hook, e os dados de origem passaram a ser
  bloqueados nesta atividade. Contrato de API não tem, e não dá para ter: nenhum hook consegue
  decidir se `{"knn": ..., "decision_tree": ...}` é melhor que `{"predictions": {...}}`;
* é uma decisão **irreversível para quem consome**, diferente de código interno, que se refatora
  sem avisar ninguém;
* é uma decisão de **produto**, não de implementação. O agente tem opinião técnica sobre ela, mas
  não tem contexto sobre quem vai consumir a API nem sobre o que a disciplina vai exigir depois;
* o projeto tem precedente: a change `knn-persona-classifier` já quebrou este mesmo endpoint de
  propósito (removeu o `player_id` do path). Quebras de contrato são normais aqui — o que não pode
  ser normal é acontecerem sem decisão humana.

### Simulação do checkpoint

**Ponto de parada:** ao terminar a change OpenSpec da Árvore de Decisão e antes de escrever a
primeira linha de `decision_tree.py` ou de alterar `PersonaResponse`.

**O que o agente apresentou:** quatro formatos de resposta, cada um com o JSON concreto e o
trade-off:

| Opção | Formato | Trade-off apresentado |
|---|---|---|
| A (recomendada pelo agente) | `{"player_id": ..., "predictions": {"knn": ..., "decision_tree": ...}}` | simétrica e extensível; quebra o contrato atual |
| B | `{"player_id": ..., "persona": ..., "persona_decision_tree": ...}` | não quebra clientes; assimétrica, o KNN vira "o principal" por acidente |
| C | `{"player_id": ..., "predictions": [{"model": ..., "persona": ...}]}` | dá espaço para confiança/versão do modelo depois; mais verboso |
| D | híbrido: `persona` legado + `predictions` | compatível e simétrico; duplica a predição do KNN na mesma resposta |

**Decisão tomada: EDITAR.** O desenvolvedor não escolheu nenhuma das quatro. Resposta literal:

> *"Em vez de ser `{"player_id": "player_0001", "persona": "Killer"}` como está hoje, vamos
> modificar para o formato `{"player_id": "player_0001", "knn": "Killer", "decision_tree":
> "Explorer"}`. Ou seja, adicionando os modelos como chaves e suas predições como valores."*

Ou seja: a simetria da opção A, mas **plana**, sem o nível `predictions`.

**Justificativa da decisão (do desenvolvedor):** formato mais simples de consumir e de ler na
documentação interativa do FastAPI. O custo aceito é que um terceiro modelo passa a exigir um campo
novo no schema em vez de apenas uma chave nova em um dicionário — aceitável porque o conjunto de
modelos é decidido em tempo de código, não em runtime.

**O que aconteceu depois:** a decisão foi registrada no `design.md` da change antes da implementação
e o código foi escrito já no formato aprovado. `PersonaResponse` tem hoje exatamente
`player_id`, `knn` e `decision_tree`.

### Papel humano assumido

**Revisor com poder de decisão sobre contrato e arquitetura — não revisor de diff.**

O desenvolvedor não leu linha a linha os ~1200 acrescentados nesta atividade. Ele decidiu:

1. o **contrato** da resposta do endpoint (este checkpoint);
2. a **arquitetura** — determinou que houvesse um núcleo compartilhado em `ml/` em vez de dois
   módulos duplicados, quando o agente havia apenas sinalizado a escolha;
3. o **escopo do modelo novo** — a ideia de usar Árvore de Decisão, e o módulo onde ela deveria
   morar (`src/player_modeling/ml/decision_tree.py`);
4. o **desbloqueio do agente** quando o hook mal configurado derrubou a sessão (Etapa 1).

Justificativa para esse papel, e não para revisão integral: revisar 1200 linhas linha a linha teria
consumido mais tempo do que escrevê-las, e produziria pior resultado — a atenção humana se esgota
em detalhes de estilo que `ruff`, `mypy` e 208 testes já verificam mecanicamente, e sobra pouca para
as decisões que nenhuma ferramenta verifica. O harness cobre o que é mecânico; o humano cobre o que
é irreversível. O ponto de atenção honesto é que esse arranjo **depende** da qualidade do harness:
onde não há teste nem hook, não há revisão nenhuma — foi exatamente o que aconteceu com
`evaluate_model.py`, que viveu três commits sem um único teste sem que nada reclamasse.
