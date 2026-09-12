"""Classificador KNN de perfis de jogador na Taxonomia de Bartle.

Módulo de biblioteca: importá-lo não lê o dataset nem treina nada. O
treino é disparado explicitamente por `train_classifier`, que a API chama
uma única vez na inicialização (ver ADR 0010), e a inferência por
requisição usa `predict_persona` com os artefatos já treinados.

`evaluate_classifier` existe para medir a qualidade do modelo em testes e
análises; ela não participa do caminho de inicialização nem de requisição,
porque o modelo que serve a API é treinado com o dataset completo.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler

from player_modeling.api.schemas import BartlePersona

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

N_NEIGHBORS = 5

DEFAULT_TEST_SIZE = 0.3

DEFAULT_RANDOM_STATE = 42


@dataclass(frozen=True)
class PersonaClassifier:
    """Artefatos treinados necessários para prever a persona de um jogador.

    :param model: classificador KNN já ajustado.
    :param scaler: normalizador ajustado às features de treino.
    :param label_encoder: codificador dos rótulos da Taxonomia de Bartle.
    :param feature_columns: ordem das colunas de feature usada no treino,
        que a predição deve reproduzir.
    """

    model: KNeighborsClassifier
    scaler: StandardScaler
    label_encoder: LabelEncoder
    feature_columns: tuple[str, ...]


@dataclass(frozen=True)
class ClassifierEvaluation:
    """Resultado da avaliação do classificador em um conjunto de teste.

    :param accuracy: acurácia no conjunto de teste, entre 0.0 e 1.0.
    :param report: relatório de classificação por persona (precision,
        recall, f1-score), como texto.
    :param classes: rótulos de persona presentes no dataset avaliado.
    """

    accuracy: float
    report: str
    classes: tuple[str, ...]


def load_dataset(dataset_path: Path | None = None) -> pd.DataFrame:
    """Carrega o dataset sintético rotulado usado para treinar o classificador.

    Somente leitura: o arquivo de origem nunca é alterado.

    :param dataset_path: caminho alternativo do CSV (útil em testes); usa
        `DATASET_PATH` se omitido.

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
    """Treina o classificador KNN com todas as linhas do dataset rotulado.

    Usa o dataset completo (sem reservar conjunto de teste) porque o
    objetivo é servir inferência; a medição de qualidade é feita por
    `evaluate_classifier`.

    :param dataset_path: caminho alternativo do CSV (útil em testes); usa
        `DATASET_PATH` se omitido.

    :return: artefatos treinados prontos para `predict_persona`.
    """
    frame = load_dataset(dataset_path)
    features = frame.loc[:, list(FEATURE_COLUMNS)]
    labels = frame[LABEL_COLUMN]

    label_encoder = LabelEncoder()
    encoded_labels = label_encoder.fit_transform(labels)

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    model = KNeighborsClassifier(n_neighbors=N_NEIGHBORS)
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
    :param features: features agregadas de um lote/sessão, no formato
        produzido por `player_modeling.worker.features.extract_features`
        e persistido em `player_features`, sem `session_id`/`player_id`.

    :return: persona prevista na Taxonomia de Bartle.
    :raises ValueError: se `features` não contiver exatamente as colunas
        usadas no treino, ou se o rótulo previsto não pertencer à
        Taxonomia de Bartle.
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

    Divisão estratificada pelos rótulos, para preservar a proporção de
    personas entre treino e teste. Não é usada pela API em execução.

    :param dataset_path: caminho alternativo do CSV (útil em testes); usa
        `DATASET_PATH` se omitido.
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

    model = KNeighborsClassifier(n_neighbors=N_NEIGHBORS)
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
