"""Acesso ao banco de dados compartilhado pelos processos do projeto.

Infraestrutura, não domínio: conhece `sqlite3` e variáveis de ambiente.
Usada pela API, pelo worker subscriber e pelas migrações Alembic — nenhum
deles precisa depender dos outros para abrir uma conexão.

O schema é responsabilidade exclusiva das migrações (ADR 0006).
"""
