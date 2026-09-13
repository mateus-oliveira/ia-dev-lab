"""Classificador de perfis de jogador por Árvore de Decisão (Taxonomia de Bartle).

Segundo modelo servido pela API, ao lado do KNN (ADR 0010). Aprende regras
por limiar em cada feature (`pct_attack > 0.4`, `avg_decision_time_ms < 800`)
em vez de vizinhança no espaço normalizado, e portanto erra em situações
diferentes: a divergência entre os dois modelos é justamente o sinal de
interesse para Player Modeling.

Contém apenas o que é específico da árvore: os hiperparâmetros, a construção
do estimador e a chave do modelo no contrato da API. Todo o resto vem de
`player_modeling.ml.persona_model`, compartilhado com os demais modelos.

Módulo de biblioteca: importá-lo não lê o dataset nem treina nada.
"""

from pathlib import Path

from sklearn.tree import DecisionTreeClassifier

from player_modeling.ml.persona_model import (
    DATASET_PATH,
    DEFAULT_RANDOM_STATE,
    DEFAULT_TEST_SIZE,
    FEATURE_COLUMNS,
    LABEL_COLUMN,
    ClassifierEvaluation,
    PersonaClassifier,
    evaluate_persona_classifier,
    load_dataset,
    predict_persona,
    train_persona_classifier,
)

__all__ = [
    "DATASET_PATH",
    "DEFAULT_RANDOM_STATE",
    "DEFAULT_TEST_SIZE",
    "FEATURE_COLUMNS",
    "LABEL_COLUMN",
    "MAX_DEPTH",
    "MODEL_KEY",
    "ClassifierEvaluation",
    "PersonaClassifier",
    "build_estimator",
    "evaluate_classifier",
    "load_dataset",
    "predict_persona",
    "train_classifier",
]

MODEL_KEY = "decision_tree"

MAX_DEPTH = 6


def build_estimator() -> DecisionTreeClassifier:
    """Constrói uma árvore de decisão nova, com os hiperparâmetros do projeto.

    `max_depth` limitado evita que a árvore memorize o dataset sintético,
    cuja separação entre personas é bastante nítida; `random_state` fixo
    mantém a reprodutibilidade adotada no resto do projeto.

    :return: árvore de decisão não ajustada.
    """
    return DecisionTreeClassifier(max_depth=MAX_DEPTH, random_state=DEFAULT_RANDOM_STATE)


def train_classifier(dataset_path: Path | None = None) -> PersonaClassifier[DecisionTreeClassifier]:
    """Treina a árvore de decisão com todas as linhas do dataset rotulado.

    :param dataset_path: caminho alternativo do CSV (útil em testes); usa
        `DATASET_PATH` se omitido.

    :return: artefatos treinados prontos para `predict_persona`.
    """
    return train_persona_classifier(build_estimator(), dataset_path)


def evaluate_classifier(
    dataset_path: Path | None = None,
    test_size: float = DEFAULT_TEST_SIZE,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> ClassifierEvaluation:
    """Avalia a árvore de decisão em um conjunto de teste separado do treino.

    :param dataset_path: caminho alternativo do CSV (útil em testes); usa
        `DATASET_PATH` se omitido.
    :param test_size: fração do dataset reservada para teste.
    :param random_state: semente da divisão, para reprodutibilidade.

    :return: acurácia, relatório de classificação e rótulos avaliados.
    """
    return evaluate_persona_classifier(build_estimator, dataset_path, test_size, random_state)
