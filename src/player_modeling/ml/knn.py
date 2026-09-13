"""Classificador KNN de perfis de jogador na Taxonomia de Bartle.

Contém apenas o que é específico do KNN: o hiperparâmetro `N_NEIGHBORS`, a
construção do estimador e a chave do modelo no contrato da API. Carga do
dataset, escalonamento, codificação de rótulos, predição e avaliação vêm de
`player_modeling.ml.persona_model`, compartilhados com os demais modelos.

Módulo de biblioteca: importá-lo não lê o dataset nem treina nada. O treino
é disparado explicitamente por `train_classifier`, que a API chama uma única
vez na inicialização (ver ADR 0010), e a inferência por requisição usa
`predict_persona` com os artefatos já treinados.
"""

from pathlib import Path

from sklearn.neighbors import KNeighborsClassifier

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
    "MODEL_KEY",
    "N_NEIGHBORS",
    "ClassifierEvaluation",
    "PersonaClassifier",
    "build_estimator",
    "evaluate_classifier",
    "load_dataset",
    "predict_persona",
    "train_classifier",
]

MODEL_KEY = "knn"

N_NEIGHBORS = 5


def build_estimator() -> KNeighborsClassifier:
    """Constrói um KNN novo, com os hiperparâmetros do projeto.

    Devolve sempre uma instância limpa: reaproveitar um estimador já
    ajustado entre treino e avaliação misturaria estados.

    :return: classificador KNN não ajustado.
    """
    return KNeighborsClassifier(n_neighbors=N_NEIGHBORS)


def train_classifier(dataset_path: Path | None = None) -> PersonaClassifier[KNeighborsClassifier]:
    """Treina o classificador KNN com todas as linhas do dataset rotulado.

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
    """Avalia o KNN em um conjunto de teste separado do treino.

    :param dataset_path: caminho alternativo do CSV (útil em testes); usa
        `DATASET_PATH` se omitido.
    :param test_size: fração do dataset reservada para teste.
    :param random_state: semente da divisão, para reprodutibilidade.

    :return: acurácia, relatório de classificação e rótulos avaliados.
    """
    return evaluate_persona_classifier(build_estimator, dataset_path, test_size, random_state)
