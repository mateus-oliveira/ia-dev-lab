"""Classificador de perfis de jogador por Árvore de Decisão (Taxonomia de Bartle).

Segundo modelo servido pela API, ao lado do KNN (ADR 0010). Aprende regras
por limiar em cada feature (`pct_attack > 0.4`, `avg_decision_time_ms <
800`) em vez de vizinhança no espaço normalizado, e portanto erra em
situações diferentes: a divergência entre os dois modelos é justamente o
sinal de interesse.

Módulo de biblioteca: importá-lo não lê o dataset nem treina nada.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from player_modeling.api.schemas import BartlePersona

MODEL_KEY = "decision_tree"

DATASET_PATH = Path(__file__).resolve().parents[2] / "data" / "sessions_features.csv"

FEATURE_COLUMNS: tuple[str, ...] = (
    "n_events",
    "pct_attack",
    "pct_explore",
    "pct_social",
    "pct_quest_complete",
    "pct_retry",
    "avg_decision_time_ms",
    "fail_rate",
)

LABEL_COLUMN = "true_persona"

MAX_DEPTH = 6

DEFAULT_TEST_SIZE = 0.3

DEFAULT_RANDOM_STATE = 42


@dataclass(frozen=True)
class PersonaClassifier:
    """Artefatos treinados necessários para prever a persona de um jogador.

    :param model: árvore de decisão já ajustada.
    :param scaler: normalizador ajustado às features de treino.
    :param label_encoder: codificador dos rótulos da Taxonomia de Bartle.
    :param feature_columns: ordem das colunas de feature usada no treino.
    """

    model: DecisionTreeClassifier
    scaler: StandardScaler
    label_encoder: LabelEncoder
    feature_columns: tuple[str, ...]


@dataclass(frozen=True)
class ClassifierEvaluation:
    """Resultado da avaliação do classificador em um conjunto de teste.

    :param accuracy: acurácia no conjunto de teste, entre 0.0 e 1.0.
    :param report: relatório de classificação por persona, como texto.
    :param classes: rótulos de persona presentes no dataset avaliado.
    """

    accuracy: float
    report: str
    classes: tuple[str, ...]


def build_estimator() -> DecisionTreeClassifier:
    """Constrói uma árvore de decisão nova, com os hiperparâmetros do projeto.

    Devolve sempre uma instância limpa: reaproveitar um estimador já
    ajustado entre treino e avaliação misturaria estados.

    :return: árvore de decisão não ajustada.
    """
    return DecisionTreeClassifier(max_depth=MAX_DEPTH, random_state=DEFAULT_RANDOM_STATE)


def load_dataset(dataset_path: Path | None = None) -> pd.DataFrame:
    """Carrega o dataset sintético rotulado usado para treinar o classificador.

    :param dataset_path: caminho alternativo do CSV (útil em testes).

    :return: DataFrame com as colunas de feature e a coluna-rótulo.
    :raises FileNotFoundError: se o dataset não existir no caminho usado.
    :raises ValueError: se faltar alguma coluna esperada no dataset.
    """
    path = dataset_path or DATASET_PATH
    if not path.is_file():
        raise FileNotFoundError(
            f"Dataset de treino não encontrado em '{path}'. Gere-o com "
            "`python src/player_modeling/scripts/generate_raw_events.py`."
        )

    frame = pd.read_csv(path)
    expected_columns = (*FEATURE_COLUMNS, LABEL_COLUMN)
    missing = [column for column in expected_columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Dataset '{path}' não possui as colunas obrigatórias: {missing}.")

    return frame


def train_classifier(dataset_path: Path | None = None) -> PersonaClassifier:
    """Treina a árvore de decisão com todas as linhas do dataset rotulado.

    :param dataset_path: caminho alternativo do CSV (útil em testes).

    :return: artefatos treinados prontos para `predict_persona`.
    """
    frame = load_dataset(dataset_path)
    features = frame.loc[:, list(FEATURE_COLUMNS)]
    labels = frame[LABEL_COLUMN]

    label_encoder = LabelEncoder()
    encoded_labels = label_encoder.fit_transform(labels)

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    model = build_estimator()
    model.fit(scaled_features, encoded_labels)

    return PersonaClassifier(
        model=model,
        scaler=scaler,
        label_encoder=label_encoder,
        feature_columns=FEATURE_COLUMNS,
    )


def predict_persona(classifier: PersonaClassifier, features: Mapping[str, Any]) -> BartlePersona:
    """Prevê a persona de um jogador a partir de suas features agregadas.

    :param classifier: artefatos devolvidos por `train_classifier`.
    :param features: features agregadas de um lote/sessão.

    :return: persona prevista na Taxonomia de Bartle.
    :raises ValueError: se `features` não contiver exatamente as colunas do treino.
    """
    row = _build_feature_row(classifier.feature_columns, features)
    scaled_row = classifier.scaler.transform(row)
    encoded_prediction = classifier.model.predict(scaled_row)
    label = str(classifier.label_encoder.inverse_transform(encoded_prediction)[0])
    return BartlePersona(label)


def evaluate_classifier(
    dataset_path: Path | None = None,
    test_size: float = DEFAULT_TEST_SIZE,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> ClassifierEvaluation:
    """Avalia o classificador em um conjunto de teste separado do treino.

    :param dataset_path: caminho alternativo do CSV (útil em testes).
    :param test_size: fração do dataset reservada para teste.
    :param random_state: semente da divisão, para reprodutibilidade.

    :return: acurácia, relatório de classificação e rótulos avaliados.
    """
    frame = load_dataset(dataset_path)
    features = frame.loc[:, list(FEATURE_COLUMNS)]
    labels = frame[LABEL_COLUMN]

    label_encoder = LabelEncoder()
    encoded_labels = label_encoder.fit_transform(labels)

    features_train, features_test, labels_train, labels_test = train_test_split(
        features,
        encoded_labels,
        test_size=test_size,
        random_state=random_state,
        stratify=encoded_labels,
    )

    scaler = StandardScaler()
    scaled_train = scaler.fit_transform(features_train)
    scaled_test = scaler.transform(features_test)

    model = build_estimator()
    model.fit(scaled_train, labels_train)
    predictions = model.predict(scaled_test)

    class_names = tuple(str(name) for name in label_encoder.classes_)
    return ClassifierEvaluation(
        accuracy=float(accuracy_score(labels_test, predictions)),
        report=str(classification_report(labels_test, predictions, target_names=class_names)),
        classes=class_names,
    )


def _build_feature_row(
    feature_columns: tuple[str, ...], features: Mapping[str, Any]
) -> pd.DataFrame:
    """Monta a linha de features na ordem do treino, validando o conjunto recebido.

    :param feature_columns: colunas de feature esperadas, na ordem do treino.
    :param features: features recebidas para predição.

    :return: DataFrame de uma linha com as colunas na ordem do treino.
    :raises ValueError: se houver feature faltando ou não reconhecida.
    """
    expected = set(feature_columns)
    received = set(features)
    missing = sorted(expected - received)
    unexpected = sorted(received - expected)
    if missing or unexpected:
        raise ValueError(
            "Features incompatíveis com o classificador treinado "
            f"(faltando: {missing}; não reconhecidas: {unexpected})."
        )

    return pd.DataFrame([{column: features[column] for column in feature_columns}])
