## 1. Script de verificação

- [x] 1.1 Criar `scripts/check_readme_tree_granularity.py` implementando o parser de profundidade do bloco de árvore ASCII do `README.md` (identifica o bloco ```` ```text ```` da árvore, classifica cada linha como diretório/arquivo e calcula a profundidade) e a checagem de granularidade (arquivo só permitido em profundidade 1), com `main()` retornando código de saída != 0 em caso de violação e imprimindo as linhas inválidas em `stderr`, seguindo o estilo/docstrings de `scripts/check_sensitive_paths.py`.
- [x] 1.2 Adicionar `src/tests/scripts/test_check_readme_tree_granularity.py` cobrindo: árvore só com diretórios e arquivos de raiz (aprovado), árvore com um arquivo em subdiretório (falha, mensagem identifica a linha), README sem bloco de árvore (não aplicável / aprovado), e a árvore real do README após a correção da tarefa 3.1 (regressão) — verificar com `poetry run pytest src/tests/scripts/test_check_readme_tree_granularity.py`.

## 2. Harness (pré-commit)

- [x] 2.1 Registrar o novo hook `check-readme-tree-granularity` em `.pre-commit-config.yaml` (entry `poetry run python scripts/check_readme_tree_granularity.py`, `pass_filenames: false`), seguindo o padrão do hook `check-sensitive-paths` — verificar com `poetry run pre-commit run check-readme-tree-granularity --all-files`.

## 3. Correção do README e documentação

- [x] 3.1 Reescrever o bloco de árvore da seção "Estrutura do projeto" em `README.md`, colapsando `docs/adr/`, `scripts/` e todos os subdiretórios de `src/` para não listarem arquivos individuais (apenas diretórios e os arquivos de raiz do projeto) — verificar rodando `poetry run python scripts/check_readme_tree_granularity.py` manualmente sobre o README atualizado.
- [x] 3.2 Criar ADR em `docs/adr/` (próximo número sequencial após 0008) documentando a decisão de granularidade da árvore do README (regra, motivação, alternativas rejeitadas — ver design.md - Decisions) e referenciá-la no comentário/seção relevante do harness se aplicável.
- [x] 3.3 Atualizar a seção de comandos do harness em `CLAUDE.md` (lista de verificações de pré-commit) para mencionar o novo hook, mantendo consistência com o restante do documento.

## 4. Validação final

- [x] 4.1 Rodar `poetry run pytest` e `poetry run pre-commit run --all-files` e confirmar que todos os testes e hooks passam, incluindo o novo hook contra o `README.md` já corrigido.
- [x] 4.2 Rodar `poetry run python scripts/report_scope_diff.py` (branch base `dev`) e confirmar que apenas os arquivos esperados por esta change (script, teste, `.pre-commit-config.yaml`, `README.md`, `CLAUDE.md`, novo ADR) aparecem no diff.
