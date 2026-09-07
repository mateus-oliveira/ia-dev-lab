# **Player Modeling Lab**

## Sobre o projeto

### Objetivo

Este projeto é uma Prova de Conceito (POC) para experimentação de **Player Modeling**, com foco na utilização de Engenharia de Dados e Machine Learning para representar e analisar o comportamento de jogadores.

O projeto terá evolução incremental ao longo da disciplina **PPGTI1101** utilizando ferramentas de Inteligência Artificial como apoio ao desenvolvimento, análise, testes, documentação e evolução da arquitetura.

### Objetivo inicial

A primeira versão do projeto deve implementar uma _pipeline_ simples capaz de:

1. Receber eventos brutos de jogadores em formato JSON ou CSV.
2. Validar e processar esses eventos.
3. Realizar transformações e agregações.
4. Gerar features comportamentais por jogador.
5. Persistir os dados processados em formato adequado para análise posterior.

Fluxo inicial:

```text
Eventos brutos
      ↓
Validação
      ↓
Extract
      ↓
Transform
      ↓
Feature Engineering
      ↓
Dados processados
```

### Evolução planejada

O projeto deverá ser desenvolvido de maneira incremental. Futuras versões poderão adicionar:

* API REST para consulta dos dados dos jogadores;
* banco de dados;
* pipelines de Machine Learning;
* previsão de comportamentos dos jogadores;
* análise de importância das features;
* técnicas de explicabilidade;
* integração com fontes externas de eventos, como plataformas de jogos;
* experimentos de Player Modeling.

Essas funcionalidades **não devem ser implementadas antecipadamente** sem uma solicitação explícita.

---

## Comandos

### Criar ambiente virtual

```bash
python3.13 -m venv venv
```

### Ativar ambiente no Linux/macOS

```bash
source venv/bin/activate
```

### Instalar dependências

```bash
pip install -r requirements.txt
```

### Executar testes

```bash
pytest
```

### Executar um teste específico

```bash
pytest tests/test_nome_do_teste.py
```

### Executar o pipeline

```bash
python -m player_modeling
```

Caso a estrutura de execução seja alterada durante o desenvolvimento, atualizar este arquivo e o README.md.

---

## Convenções de código

### Linguagem

O projeto utiliza **Python 3.13**.

### Estilo

Seguir PEP 8 e priorizar código:

* simples;
* legível;
* modular;
* testável;
* com responsabilidades bem definidas.

### Tipagem

Utilizar type hints nas funções e métodos.

Exemplo:

```python
def calculate_playtime(events: list[dict]) -> float:
    ...
```

### Comentários

Evitar comentários gigantes ou no meio do código.
A regra é que os comentários de uma classe, função ou método estejam na docstring com o seguinte formato:

```python
def sum_values(a: int, b: int) -> int:
      """Sum two integers then return it.

      :param a: The first value to the operation.
      :param b: The second value to sum with first.

      :return: the result of a + b.
      """
      return a + b
```

### Nomenclatura

Utilizar:

* `snake_case` para funções e variáveis;
* `PascalCase` para classes;
* `UPPER_CASE` para constantes;
* nomes descritivos relacionados ao domínio de Player Modeling.

Exemplo:

```python
player_id
session_count
playtime_hours
items_collected
```

### Organização

Organizar o código preferencialmente por **domínio ou funcionalidade**, e não apenas por tipo técnico.

Exemplo:

```text
src/
└── player_modeling/
    ├── ingestion/
    ├── transformation/
    ├── features/
    └── api/
```

### Dados

Os dados devem ser separados em diferentes estágios:

```text
data/
├── raw/
└── processed/
```

`raw/` deve conter dados brutos e não modificados.

`processed/` deve conter dados após as etapas de transformação e feature engineering.

### Testes

Toda funcionalidade relevante deve possuir testes automatizados.

Os testes devem estar dentro de:

```text
tests/
```

Preferir testes unitários para funções de transformação e geração de features.

### Documentação

Alterações arquiteturais relevantes devem ser registradas em:

```text
docs/adr/
```

Decisões importantes devem ser documentadas por meio de Architecture Decision Records (ADR).

---

## Não fazer

### Não implementar funcionalidades futuras sem solicitação

Não implementar automaticamente:

* Machine Learning;
* API;
* banco de dados;
* integração com PlayFab;
* integração com Databricks;
* Redis;
* infraestrutura de produção;
* deploy;

se essas funcionalidades ainda não fizerem parte da atividade atual.

### Não utilizar dados reais de jogadores

Durante a fase inicial, utilizar **dados sintéticos**.

Não incluir informações pessoais, identificáveis ou sensíveis de jogadores.

### Não modificar dados brutos

Arquivos dentro de:

```text
data/raw/
```

devem ser tratados como dados de origem e não devem ser sobrescritos pelo pipeline.

### Não gerar código sem considerar a arquitetura existente

Antes de criar ou modificar código:

1. analisar a estrutura atual do projeto;
2. verificar arquivos relacionados;
3. respeitar as convenções deste documento;
4. verificar testes existentes;
5. evitar duplicação de funcionalidades.

### Não adicionar dependências desnecessárias

Antes de adicionar uma biblioteca, avaliar se a funcionalidade pode ser implementada utilizando as dependências existentes.

Quando uma nova dependência for necessária, explicar sua finalidade.

### Não ignorar testes

Não considerar uma funcionalidade concluída sem verificar se os testes existentes continuam passando.

### Não substituir decisões do desenvolvedor sem justificativa

A IA deve apresentar alternativas e explicar trade-offs quando houver decisões arquiteturais relevantes.

A decisão final sobre alterações significativas deve permanecer com o desenvolvedor.

---

## Princípios para desenvolvimento assistido por IA

A Inteligência Artificial deve ser utilizada como **assistente de desenvolvimento**, não como substituta da revisão humana.

Ao gerar ou modificar código:

1. compreender o contexto existente;
2. propor a solução;
3. implementar somente após avaliar a abordagem;
4. executar ou propor testes;
5. verificar o resultado;
6. explicar alterações relevantes.

Código gerado por IA deve ser revisado antes de ser considerado parte definitiva do projeto.

O projeto deve priorizar **incrementalidade**, permitindo que novas atividades da disciplina adicionem funcionalidades sem exigir uma reestruturação completa da aplicação.
