# ADR 0004 - DB e primeira tabela users

* *Status:* Aceito
* *Data:* 2026-09-11
* *Decisão:* Usar o `db.slite3` para facilitar o desenvolvimento.

## Decisões

O arquivo `db.sqlite3` deve ficar na raiz do projeto, e deve ser ignorado no `.gitignore`.
    
Lembrar de atualizar as variáveis no `.env.example`.

A primeira tabela estabelecida foi `users`, com o seguinte formato:

```sql
id: int PK
name: VARCHAR
username: VARCHAR -- ver em session_feature
password: VARCHAR -- criptografada
```