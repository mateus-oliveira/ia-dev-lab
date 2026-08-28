# Player Modeling Lab

POC experimental para **Modelagem de Jogadores (Player Modeling)** utilizando Engenharia de Dados e, posteriormente, Machine Learning.

O projeto faz parte da disciplina **PPGTI1101**, do Programa de Pós-Graduação em Tecnologia da Informação (PPgTI/UFRN), e será desenvolvido de forma incremental ao longo da disciplina.

## Objetivo

O objetivo inicial é construir uma pipeline capaz de transformar eventos brutos de jogadores em **features comportamentais agregadas por jogador**.

A ideia é utilizar esse projeto como um laboratório para experimentar técnicas de Engenharia de Dados, Machine Learning e desenvolvimento de software assistido por Inteligência Artificial.

### Pipeline inicial

```text
Eventos brutos
      │
      ▼
 Validação
      │
      ▼
   Extract
      │
      ▼
  Transform
      │
      ▼
Feature Engineering
      │
      ▼
Dados processados
```

## Escopo inicial

A primeira versão do projeto trabalhará com dados sintéticos de jogadores.

Os eventos poderão representar comportamentos como:

* início de uma sessão;
* encerramento de uma sessão;
* coleta de itens;
* compras;
* aquisição de skins;
* progressão no jogo;
* tempo de jogo.

A partir desses eventos, serão calculadas características comportamentais, como:

* quantidade de sessões;
* tempo total de jogo;
* quantidade de itens coletados;
* quantidade de compras;
* valor total gasto;
* frequência de sessões;
* outras métricas derivadas dos eventos.

## Evolução planejada

O projeto será desenvolvido incrementalmente durante a disciplina.

Funcionalidades futuras poderão incluir:

1. Pipeline de Engenharia de Dados mais completa;
2. API REST para consulta das informações dos jogadores;
3. persistência em banco de dados;
4. Feature Engineering mais avançado;
5. modelos de Machine Learning;
6. previsão de comportamentos dos jogadores;
7. análise de importância das features;
8. técnicas de explicabilidade;
9. integração com plataformas de jogos;
10. experimentos relacionados à pesquisa de Player Modeling.

Essas funcionalidades serão adicionadas conforme o projeto evoluir e as atividades da disciplina forem realizadas.

## Estrutura do projeto

```text
player-modeling-lab/
│
├── CLAUDE.md
├── README.md
├── requirements.txt
│
├── docs/
│   ├── adr/
│   │   └── 0001-escolha-da-ferramenta-de-ia.md
│   └── prompts-comparacao.md
│
├── data/
│   ├── raw/
│   └── processed/
│
├── src/
│   └── player_modeling/
│       ├── ingestion/
│       ├── transformation/
│       ├── features/
│       └── api/
│
└── tests/
```

### Organização dos diretórios

| Diretório                             | Responsabilidade                       |
| ------------------------------------- | -------------------------------------- |
| `src/`                                | Código-fonte da aplicação              |
| `src/player_modeling/ingestion/`      | Entrada e leitura dos eventos          |
| `src/player_modeling/transformation/` | Transformação dos dados                |
| `src/player_modeling/features/`       | Geração de features comportamentais    |
| `src/player_modeling/api/`            | Endpoints da API, quando implementados |
| `data/raw/`                           | Dados brutos de entrada                |
| `data/processed/`                     | Dados após processamento               |
| `tests/`                              | Testes automatizados                   |
| `docs/adr/`                           | Architecture Decision Records          |
| `docs/`                               | Documentação complementar              |

## Tecnologias

A versão inicial utiliza:

* **Python 3.13**
* **Pandas**
* **Pydantic**
* **Pytest**
* **Git**
* **GitHub**

A stack poderá ser ampliada conforme as necessidades das próximas etapas do projeto.

## Instalação

Clone o repositório:

```bash
git clone <URL_DO_REPOSITORIO>
cd ia-dev-lab
```

Crie o ambiente virtual:

```bash
python3.13 -m venv venv
```

Ative o ambiente virtual no Linux/macOS:

```bash
source venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Executando os testes

Execute todos os testes com:

```bash
pytest
```

Para executar um arquivo de teste específico:

```bash
pytest tests/test_nome_do_teste.py
```

## Executando o pipeline

A execução do pipeline será realizada por meio do módulo principal do projeto:

```bash
python -m player_modeling
```

Os comandos poderão ser atualizados conforme a estrutura de execução evoluir.

## Dados

A versão inicial utiliza **dados sintéticos**.

Os dados de entrada devem ser armazenados em:

```text
data/raw/
```

Os resultados processados devem ser armazenados em:

```text
data/processed/
```

Os dados brutos não devem ser sobrescritos pelo pipeline.

## Desenvolvimento assistido por IA

A Inteligência Artificial é utilizada como ferramenta de apoio ao desenvolvimento do projeto.

Entre as atividades realizadas com auxílio de IA estão:

* geração e revisão de código;
* criação de testes;
* análise de arquitetura;
* documentação;
* refatoração;
* análise de dados;
* geração de prompts de desenvolvimento.

Todo código gerado ou modificado com auxílio de IA deve passar por revisão humana antes de ser incorporado ao projeto.

As regras e o contexto para desenvolvimento assistido por IA estão documentados em [`CLAUDE.md`](./CLAUDE.md).
