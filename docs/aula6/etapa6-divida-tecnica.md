# Etapa 6 — Dívida técnica (Opção A)

## Ferramenta e configuração

O projeto já roda `ruff` no pre-commit, mas com um conjunto deliberadamente enxuto
(`select = ["E", "F", "I", "UP", "B"]` em `pyproject.toml`) — erros, imports e bugs prováveis. A
investigação consistiu em rodar o **mesmo** linter com o ruleset completo, o que habilita entre
outros o `bandit` (regras `S*`, segurança), `flake8-datetimez` (`DTZ*`), `pylint` (`PL*`) e
`tryceratops` (`TRY*`):

```console
$ poetry run ruff check --select ALL --statistics src/player_modeling scripts
26  T201    print
18  COM812  missing-trailing-comma
13  S311    suspicious-non-cryptographic-random-usage
10  TRY003  raise-vanilla-args
 7  INP001  implicit-namespace-package
 5  EM101   raw-string-in-exception
 5  EM102   f-string-in-exception
 3  S603    subprocess-without-shell-equals-true
 3  N806    non-lowercase-variable-in-function
 2  PLR2004 magic-value-comparison
 1  S105    hardcoded-password-string
 1  S106    hardcoded-password-func-arg
 1  S608    hardcoded-sql-expression
 1  DTZ001  call-datetime-without-tzinfo
 1  DTZ005  call-datetime-now-without-tzinfo
 ... (34 regras, ~120 apontamentos)
```

A maior parte é ruído para este projeto: os 26 `print` estão em scripts de linha de comando, onde
imprimir **é** a função; os 13 `S311` são o `random` do simulador, que gera dados sintéticos e não
precisa ser criptográfico; `COM812` e `EM101/EM102` são estilo. Adotar `ALL` no harness produziria
mais supressões do que correções — o ruleset enxuto do projeto está certo como política permanente.

O valor da execução foi outro: usar o ruleset completo **uma vez**, como auditoria, para encontrar o
que o ruleset permanente não vê.

## Sinal real de dívida técnica identificado

### `S105` — segredo de assinatura de JWT embutido no código-fonte

```text
src/player_modeling/api/security.py:19:22: S105 Possible hardcoded password assigned to:
  "DEFAULT_SECRET_KEY"
```

```python
# src/player_modeling/api/security.py
DEFAULT_SECRET_KEY = "change-this-in-production-use-a-strong-secret-key-32-chars"

def get_secret_key() -> str:
    return os.getenv("JWT_SECRET_KEY", DEFAULT_SECRET_KEY)
```

O padrão "variável de ambiente com fallback embutido" é o que qualquer scaffold de FastAPI gera — e
foi exatamente o que a IA produziu quando a camada de autenticação foi implementada (ADR 0005). Ele
parece seguro porque a chave "de verdade" vem do ambiente. Não é.

E há um agravante que o linter não consegue ver: **`.env.example` distribui o mesmo valor**.

```console
$ grep -n -i secret .env.example
16:JWT_SECRET_KEY=change-this-in-production-use-a-strong-secret-key-32-chars
```

Ou seja, o caminho "correto" documentado no README — copiar `.env.example` para `.env` — reproduz
exatamente o segredo que está publicado no repositório. O fallback deixa de ser um caso de borda e
passa a ser o comportamento padrão de qualquer clone.

### Demonstração do impacto

Um atacante que só leu o código-fonte público consegue forjar um token válido para qualquer jogador,
sem jamais conhecer a senha:

```python
os.environ.pop("JWT_SECRET_KEY", None)     # cenario do fallback

# usuario registrado com uma senha que o atacante nao sabe
conn.execute("INSERT INTO users (name, username, password) VALUES (?,?,?)",
             ("Vitima", "player_0042", hash_password("uma-senha-que-o-atacante-nao-sabe")))

# o atacante assina um token com a chave que leu no repositorio
forjado = jwt.encode({"sub": "player_0042", "exp": ...}, DEFAULT_SECRET_KEY, algorithm="HS256")

client.get("/auth/me", headers={"Authorization": f"Bearer {forjado}"})
```

```console
GET /auth/me com token FORJADO -> HTTP 200
corpo: {'id': 1, 'name': 'Vitima', 'username': 'player_0042'}
```

O mesmo token dá acesso a `GET /players/me/persona`, já que a rota deriva o `player_id` do `sub` do
token (ADR 0010). O isolamento entre jogadores — que tem teste dedicado e passa — é contornável por
completo sem tocar em uma linha da lógica de autorização.

Por que nada detectou isso antes:

* os **testes passam**, porque os testes usam o mesmo `get_secret_key()` e nunca perguntam de onde a
  chave veio;
* o **pre-commit passa**, porque `S105` é regra de segurança e não está no ruleset do projeto;
* `check_sensitive_paths.py` e `detect-private-key` olham **caminhos e formatos de chave privada**,
  não uma string literal em um `.py`;
* o CI só roda `pytest`.

Este é o ponto da Etapa 6 que vale registrar: a dívida não estava escondida em código feio. Estava
em código limpo, tipado, documentado e coberto por testes — e só apareceu quando uma ferramenta com
outro critério olhou para ele.

## Mitigação proposta

**1. Remover o fallback e falhar rápido.** `get_secret_key()` deve levantar erro quando
`JWT_SECRET_KEY` não estiver definida, em vez de assinar com uma chave conhecida:

```python
def get_secret_key() -> str:
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise RuntimeError(
            "JWT_SECRET_KEY nao definida. Gere uma com: "
            "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )
    return secret
```

Uma API que não sobe é um incidente de 30 segundos; uma API que sobe com segredo público é um
incidente silencioso.

**2. Tirar o valor utilizável do `.env.example`.** Substituir por um marcador que não funcione e
que ensine a gerar o valor, forçando a ação em vez de premiar a cópia cega.

**3. Validar no startup, junto com o treino dos modelos.** O `lifespan` já interrompe a subida
quando o dataset está ausente ou inválido (ADR 0010); a mesma política deve valer para o segredo.

**4. Adicionar `S` (bandit) ao ruleset permanente do pre-commit,** com as exceções pontuais que este
projeto justifica (`S311` no simulador, `S603/S607` nos scripts de harness que invocam `git`). Isso
transforma a auditoria pontual em rede permanente e é o que impede a dívida de voltar.

**5. Manter as demais correções fora do escopo desta atividade,** registrando-as: `DTZ001/DTZ005`
(datetimes ingênuos em `created_at` de `player_features` e na geração de eventos) e o `ARG001`
(`session_index` recebido e nunca usado em `generate_session`) são dívidas reais, porém de impacto
baixo, e merecem change própria.

## O que se aprendeu

O ruleset permanente de um projeto é uma escolha de **política**, não de rigor: mais regras não é
melhor, porque um linter que aponta 120 coisas em um projeto de 2.000 linhas treina a equipe a
ignorá-lo. Mas a política enxuta tem um custo, e o custo é exatamente este achado — ele esteve ali
desde a ADR 0005, atravessou todos os commits, todo o CI e todas as revisões.

A conclusão prática não é "ligue todas as regras". É que **análise estática com ruleset amplo
funciona melhor como auditoria periódica do que como hook de pre-commit**, e que o que ela encontrar
com impacto real deve ser promovido ao ruleset permanente — que foi o que a proposta 4 acima faz com
as regras `S`.

Vale registrar também que a dívida foi **gerada por IA e revisada por humano**, e passou nos dois
crivos: o agente produziu o padrão idiomático de scaffold, e a revisão humana leu um código
plausível, bem documentado e com testes verdes. Nenhum dos dois é o culpado isolado — a lição é que
revisão humana e testes não substituem uma ferramenta com critério diferente do seu.

## Correção aplicada

O desenvolvedor decidiu corrigir na mesma atividade, em vez de registrar como dívida. Implementado
(ver ADR 0012):

* `get_secret_key()` sem valor padrão — levanta `RuntimeError` com o comando de geração na mensagem
  quando `JWT_SECRET_KEY` está ausente, vazia ou com menos de 32 caracteres;
* validação no `lifespan`, antes do treino dos modelos: configuração inválida impede a subida;
* `.env.example` com `JWT_SECRET_KEY=` vazia e o comando de geração no comentário;
* segredo de teste declarado explicitamente em `src/tests/conftest.py`, numa fixture `autouse`;
* quatro testes de regressão, incluindo um que falha se alguém voltar a colocar um valor utilizável
  no `.env.example`.

Verificação de que o ataque deixou de funcionar:

```console
$ # com JWT_SECRET_KEY ausente:
OK - bloqueado: JWT_SECRET_KEY não está definida. Gere um segredo com
  `python -c "import secrets; print(secrets.token_urlsafe(48))"` e defina-a no .env
OK - API nao sobe: JWT_SECRET_KEY não está definida...

$ poetry run pytest -q
221 passed
```

Restam dois apontamentos `S105`/`S106` — `SECRET_KEY_ENV_VAR = "JWT_SECRET_KEY"` e
`token_type="bearer"` — que são falsos positivos: a regra reconhece o formato, não o significado.
Isso confirma o ponto da proposta 4: promover `S*` ao harness permanente vai exigir supressões
pontuais, e essa decisão ficou registrada como pendente, não tomada às pressas.
