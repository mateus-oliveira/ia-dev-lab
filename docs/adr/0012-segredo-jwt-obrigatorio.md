# ADR 0012 - Segredo JWT Obrigatório, Sem Valor Padrão

* **Status:** Aceito
* **Data:** 2026-09-13
* **Decisão:** Remover o segredo de assinatura JWT embutido no código-fonte; a aplicação passa a exigir `JWT_SECRET_KEY` no ambiente e a falhar na inicialização se ela estiver ausente, vazia ou curta demais.

## Contexto

Uma auditoria de análise estática — `ruff` com o ruleset completo (`--select ALL`), habilitando as regras de segurança do `bandit`, registrada em `docs/aula6/etapa6-divida-tecnica.md` — apontou:

```text
src/player_modeling/api/security.py:19:22: S105 Possible hardcoded password assigned to:
  "DEFAULT_SECRET_KEY"
```

O código implementado junto com a camada de autenticação (ADR 0005) seguia o padrão idiomático de scaffold FastAPI:

```python
DEFAULT_SECRET_KEY = "change-this-in-production-use-a-strong-secret-key-32-chars"

def get_secret_key() -> str:
    return os.getenv("JWT_SECRET_KEY", DEFAULT_SECRET_KEY)
```

Havia um agravante que o linter não alcança: `.env.example` distribuía **o mesmo valor**. O caminho documentado no README — copiar `.env.example` para `.env` — reproduzia exatamente o segredo publicado no repositório, de modo que o fallback deixava de ser caso de borda e passava a ser o comportamento padrão de qualquer clone.

O impacto foi demonstrado, não presumido. Com a variável de ambiente ausente, um token assinado com a chave lida do repositório foi aceito:

```console
GET /auth/me com token FORJADO -> HTTP 200
corpo: {'id': 1, 'name': 'Vitima', 'username': 'player_0042'}
```

O mesmo token dá acesso a `GET /players/me/persona`, já que a rota deriva o `player_id` do `sub` do token (ADR 0010). O isolamento entre jogadores — que tem teste dedicado e passa — era contornável por completo sem tocar na lógica de autorização.

Nada no projeto detectava isso: os testes usavam a mesma função e nunca perguntavam a origem da chave; o pre-commit não tinha as regras `S*` no ruleset; `check_sensitive_paths.py` e `detect-private-key` olham caminhos e formatos de chave privada, não uma string literal em um `.py`; e o CI só roda `pytest`.

## Decisão

### `get_secret_key()` não tem valor padrão

A função lê `JWT_SECRET_KEY` do ambiente e levanta `RuntimeError` se a variável estiver ausente, vazia (ou só com espaços) ou com menos de `MIN_SECRET_KEY_LENGTH` (32) caracteres. A mensagem de erro inclui o comando que gera um segredo adequado.

### Validação na inicialização da aplicação

O `lifespan` chama `get_secret_key()` antes de treinar os modelos, aplicando ao segredo a mesma política que a ADR 0010 já aplica ao dataset: configuração inválida impede a subida do servidor, em vez de degradar requisição por requisição.

### `.env.example` não distribui valor utilizável

A linha passa a ser `JWT_SECRET_KEY=` (vazia), precedida do comentário com o comando de geração. Um teste (`test_example_env_file_ships_no_usable_secret`) falha se alguém voltar a colocar um valor ali.

### O segredo de teste é declarado nos testes

`src/tests/conftest.py` define `JWT_SECRET_KEY` em uma fixture `autouse` de sessão. O segredo usado pela suíte passa a estar visível no código de teste, que é onde ele deve estar — e não escondido como fallback no código de produção.

## Justificativa

Uma API que não sobe é um incidente de trinta segundos, resolvido por quem está olhando para o terminal. Uma API que sobe assinando tokens com um segredo público é um incidente silencioso, que pode durar o tempo que durar o projeto. Entre falhar cedo e falhar invisivelmente, a escolha é falhar cedo.

O comprimento mínimo de 32 caracteres foi escolhido por ser o tamanho da saída do HMAC-SHA256 usado pelo `HS256`: um segredo mais curto que o digest não adiciona entropia ao esquema.

Alternativas consideradas:

* *Manter o fallback apenas quando uma variável `ENVIRONMENT=development` estiver definida.* Rejeitada — cria dois caminhos de código para autenticação, e o caminho inseguro continuaria sendo o mais fácil de acionar (basta não definir nada).
* *Gerar um segredo aleatório em memória quando a variável faltar.* Rejeitada — a aplicação subiria, mas os tokens seriam invalidados a cada reinício, trocando uma falha ruidosa por um bug intermitente difícil de diagnosticar.
* *Adicionar as regras `S*` (bandit) ao ruleset permanente do pre-commit.* Não rejeitada, apenas deixada fora desta ADR: é a medida que impede a dívida de voltar, e merece decisão própria sobre as exceções que este projeto justifica (`S311` no simulador, `S603`/`S607` nos scripts de harness que invocam `git`).

## Consequências

### Positivas

* Deixa de existir um segredo válido publicado no repositório; forjar token passa a exigir acesso ao ambiente de execução.
* A configuração incorreta é detectada na subida do servidor, com mensagem acionável, e não em produção.
* Quatro testes de regressão cobrem os cenários (ausente, vazio, curto, e `.env.example` sem valor utilizável).
* O segredo de teste fica explícito no `conftest.py`, eliminando a ambiguidade sobre qual chave a suíte usa.

### Negativas / Limites

* **Mudança incompatível de operação:** a API e qualquer comando que dependa de `get_secret_key()` deixam de funcionar sem `JWT_SECRET_KEY` definida. Quem já tinha um `.env` com o valor placeholder precisa gerar um segredo novo — e todos os tokens emitidos anteriormente deixam de ser válidos.
* O `ruff` continua reportando `S105`/`S106` em duas linhas (`SECRET_KEY_ENV_VAR = "JWT_SECRET_KEY"` e `token_type="bearer"`), que são falsos positivos — a regra detecta o formato, não o significado. Isso reforça que ligar `S*` no harness exigirá supressões pontuais.
* A validação de comprimento é uma heurística: ela rejeita segredos curtos, mas não rejeita um segredo longo e previsível (`"a" * 64` passa).
* O segredo continua em variável de ambiente e arquivo `.env`. Um gerenciador de segredos apropriado é uma decisão de infraestrutura de produção, explicitamente fora do escopo atual (`CLAUDE.md`, seção "Não fazer").

## Referências

* ADR 0005 — FastAPI e autenticação JWT (origem do padrão corrigido aqui).
* ADR 0010 — treino no startup (precedente da política "configuração inválida impede a subida").
* `docs/aula6/etapa6-divida-tecnica.md` — auditoria que identificou o sinal e demonstrou o impacto.
