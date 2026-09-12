# ADR 0009 - Granularidade da Árvore de Diretórios do README

* **Status:** Aceito
* **Data:** 2026-09-12
* **Decisão:** Limitar a granularidade da árvore de diretórios do README.md a diretórios (em qualquer profundidade) e arquivos de nível raiz do projeto, e impor essa regra via hook de pré-commit.

## Contexto

A seção "Estrutura do projeto" do `README.md` mantinha uma árvore ASCII listando manualmente cada arquivo folha de código e teste (por exemplo, cada `.py` em `scripts/`, `src/player_modeling/**` e `src/tests/**`, e cada ADR em `docs/adr/`). Essa abordagem não escala: à medida que o projeto cresce (dezenas ou centenas de arquivos ao longo da disciplina PPGTI1101), a árvore precisaria ser atualizada manualmente a cada novo arquivo criado, tornando-se trabalho repetitivo e propenso a divergir da estrutura real do repositório.

O harness do projeto já impõe outras convenções de forma automatizada via hooks de pré-commit locais (ADR 0003): validação de branch, de mensagem de commit e detecção de arquivos sensíveis, cada um implementado como um script em `scripts/` sem dependências externas.

## Decisão

A árvore de diretórios do README.md pode listar:

1. **diretórios**, em qualquer profundidade (ex.: `src/player_modeling/worker/`, `docs/adr/`); e
2. **arquivos que estão diretamente na raiz do projeto** (profundidade 1 - ex.: `CLAUDE.md`, `README.md`, `docker-compose.yml`, `Makefile`).

A árvore não pode listar arquivos individuais dentro de qualquer subdiretório (profundidade 2 ou maior) - isso inclui `docs/adr/*.md`, `scripts/*.py` e qualquer caminho de arquivo sob `src/`. A responsabilidade de cada diretório continua documentada na tabela "Organização dos diretórios" do README, por diretório, não por arquivo.

Essa regra é verificada automaticamente por um novo hook de pré-commit local, `scripts/check_readme_tree_granularity.py`, que analisa o bloco de árvore ASCII do README.md e bloqueia o commit (código de saída 1) se encontrar uma entrada de arquivo em profundidade maior que a raiz do projeto. O hook é registrado em `.pre-commit-config.yaml` como `check-readme-tree-granularity`, seguindo o mesmo padrão dos demais hooks locais do harness (script Python puro, sem dependências novas, com testes espelhados em `src/tests/scripts/`).

### Alternativas consideradas

* **Lista de exceções por caminho (allowlist):** permitiria listar arquivos específicos "importantes" além da raiz. Rejeitada por reintroduzir um segundo lugar a manter atualizado manualmente, replicando o mesmo problema de escala que esta decisão busca eliminar.
* **Gerar a árvore automaticamente a partir do sistema de arquivos (ex.: `git ls-tree`) a cada commit:** resolveria o problema de forma mais completa, mas muda o README de documento editado manualmente para conteúdo gerado, uma mudança de comportamento maior e não solicitada nesta atividade. Fica registrada aqui como opção para uma change futura, caso a regra de granularidade se mostre insuficiente.
* **Permitir arquivos até uma profundidade maior (ex.: profundidade 2):** ainda escala mal, pois diretórios como `docs/adr/` crescem indefinidamente com o tempo (um arquivo por decisão arquitetural). A regra "só raiz" foi escolhida por ser a mais simples de enunciar, implementar e justificar.

## Justificativa

Restringir arquivos individuais à raiz do projeto é a regra mais simples que resolve o problema de escala sem exigir julgamento subjetivo sobre "o que é importante o suficiente para aparecer" - qualquer arquivo fora da raiz, por mais relevante que pareça, tem sua importância comunicada pela tabela de organização de diretórios ou por um ADR próprio, nunca pela árvore de arquivos. A verificação via hook, em vez de apenas uma convenção documentada, garante que a regra não seja violada silenciosamente por commits futuros (inclusive os feitos com auxílio de IA).

## Consequências

### Positivas

* A árvore do README não exige mais atualização manual a cada arquivo novo criado em `scripts/`, `docs/adr/` ou em qualquer subdiretório de `src/`.
* A regra é verificável mecanicamente, não depende de revisão humana para ser cumprida.

### Negativas / Limites

* O hook depende do formato exato da árvore ASCII usada no README (indentação de 4 espaços por nível, conectores `├──`/`└──`/`│`); uma mudança de formato exigiria ajustar o parser em `scripts/check_readme_tree_granularity.py`.
* Como os demais hooks locais do harness, pode ser contornado com `git commit --no-verify` - risco já aceito pela ADR 0003.
