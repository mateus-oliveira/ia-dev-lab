# Atividade Prática Assíncrona — Harness e Arquitetura na Prática

Documentos produzidos na atividade da Aula 6 (PPGTI1101). O relatório final consolidado está em
[`docs/relatorios/relatorio-harness-arquitetura.pdf`](../relatorios/relatorio-harness-arquitetura.pdf)
(uma página) e em [`.md`](../relatorios/relatorio-harness-arquitetura.md).

| Etapa | Documento | Conteúdo |
|---|---|---|
| 1 | [`etapa1-autonomia.md`](etapa1-autonomia.md) | Comparação entre plan mode e auto-accept (tempo, superfície de revisão, controle, risco) e justificativa do guardrail escolhido |
| 1 | [`etapa1-evidencia-hook.md`](etapa1-evidencia-hook.md) | Evidência do hook bloqueando escritas reais do agente por `Bash` e por `Write`, e o falso positivo encontrado na prática |
| 2 | [`etapa2-tdd.md`](etapa2-tdd.md) | Ciclo Red-Green-Refactor completo, tensão entre pre-commit e TDD, investigação do `tdd-guard` instalado, e comparação com/sem TDD |
| 3 | [`etapa3-checkpoint.md`](etapa3-checkpoint.md) | Checkpoint humano definido, a decisão tomada (editar a proposta do agente) e o papel humano assumido |
| 3 | [`../sessao-log.md`](../sessao-log.md) | Transcript da sessão do agente, exportado do JSONL do Claude Code |
| 4 | [`etapa4-revisao-arquitetural.md`](etapa4-revisao-arquitetural.md) | Resumo da arquitetura a partir do código real, pontos de acoplamento e decisão justificada |
| 5 | [`etapa5-diagramas.md`](etapa5-diagramas.md) | Duas versões do diagrama C4 de contêiner e comparação entre elas |
| 6 | [`etapa6-divida-tecnica.md`](etapa6-divida-tecnica.md) | Auditoria de análise estática, sinal de dívida identificado, impacto demonstrado e correção aplicada |

ADRs escritas nesta atividade:

* [ADR 0011 — Camada de Domínio e Monólito Modular](../adr/0011-camada-de-dominio-e-monolito-modular.md)
* [ADR 0012 — Segredo JWT Obrigatório, Sem Valor Padrão](../adr/0012-segredo-jwt-obrigatorio.md)
* [ADR 0003](../adr/0003-harness-desenvolvimento.md) foi atualizada com o segundo controle `PreToolUse`.

Changes OpenSpec implementadas e arquivadas: `2026-09-13-add-raw-data-write-guard`,
`2026-09-13-add-decision-tree-persona` e `2026-09-13-extract-domain-layer`.
