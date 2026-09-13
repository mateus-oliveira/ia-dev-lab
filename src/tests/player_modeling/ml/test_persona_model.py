"""Testes do núcleo compartilhado de classificação de personas.

Cobrem o que não depende do algoritmo: contrato de dados, carga do dataset,
validação estrita das features e simetria da interface entre os modelos.
"""

from pathlib import Path
from typing import Any

import pytest

from player_modeling.ml import decision_tree, knn
from player_modeling.ml.persona_model import (
    DATASET_PATH,
    FEATURE_COLUMNS,
    LABEL_COLUMN,
    load_dataset,
    predict_persona,
    train_persona_classifier,
)

MODEL_MODULES = (knn, decision_tree)


def _sample_features() -> dict[str, Any]:
    """Monta um conjunto de features válido no formato da pipeline.

    :return: dicionário com exatamente as features esperadas pelos classificadores.
    """
    return {
        "n_events": 65,
        "pct_attack": 0.092,
        "pct_explore": 0.062,
        "pct_social": 0.108,
        "pct_quest_complete": 0.154,
        "pct_retry": 0.092,
        "avg_decision_time_ms": 788.6,
        "fail_rate": 0.154,
    }


def test_dataset_path_resolves_to_source_dataset() -> None:
    """O caminho do dataset é resolvido pela localização do módulo, não pelo cwd."""
    assert DATASET_PATH.is_absolute()
    assert DATASET_PATH.is_file()
    assert DATASET_PATH.name == "sessions_features.csv"
    assert DATASET_PATH.parent.name == "data"


def test_load_dataset_reads_expected_columns() -> None:
    """O dataset carregado contém todas as features de treino e o rótulo."""
    frame = load_dataset()

    for column in (*FEATURE_COLUMNS, LABEL_COLUMN):
        assert column in frame.columns
    assert not frame.empty


def test_load_dataset_missing_file_raises(tmp_path: Path) -> None:
    """Dataset inexistente falha explicitamente em vez de treinar vazio.

    :param tmp_path: Diretório temporário fornecido pelo pytest.
    """
    with pytest.raises(FileNotFoundError):
        load_dataset(tmp_path / "inexistente.csv")


def test_load_dataset_missing_column_raises(tmp_path: Path) -> None:
    """Dataset sem uma coluna obrigatória falha explicitamente.

    :param tmp_path: Diretório temporário fornecido pelo pytest.
    """
    incomplete = tmp_path / "incompleto.csv"
    incomplete.write_text("n_events,true_persona\n10,Killer\n", encoding="utf-8")

    with pytest.raises(ValueError, match="colunas obrigatórias"):
        load_dataset(incomplete)


@pytest.mark.parametrize("module", MODEL_MODULES, ids=lambda m: str(m.MODEL_KEY))
def test_every_model_exposes_the_same_interface(module: Any) -> None:
    """Todo módulo de modelo expõe a mesma interface pública.

    É essa simetria que permite tratar os modelos de forma uniforme na API e
    no script de avaliação, e que faz de um terceiro modelo apenas um arquivo
    novo.

    :param module: Módulo de modelo sob teste.
    """
    for attribute in ("MODEL_KEY", "build_estimator", "train_classifier", "evaluate_classifier"):
        assert hasattr(module, attribute)
    assert isinstance(module.MODEL_KEY, str)


def test_model_keys_are_unique() -> None:
    """Cada modelo tem uma chave distinta, porque ela nomeia um campo da resposta."""
    keys = [module.MODEL_KEY for module in MODEL_MODULES]

    assert len(keys) == len(set(keys))


@pytest.mark.parametrize("module", MODEL_MODULES, ids=lambda m: str(m.MODEL_KEY))
def test_every_model_trains_on_the_same_feature_contract(module: Any) -> None:
    """Todos os modelos treinam sobre exatamente as mesmas colunas de feature.

    :param module: Módulo de modelo sob teste.
    """
    classifier = module.train_classifier()

    assert classifier.feature_columns == FEATURE_COLUMNS


def test_train_persona_classifier_accepts_any_estimator() -> None:
    """O núcleo treina qualquer estimador scikit-learn, sem conhecer o algoritmo.

    Garante que adicionar um modelo novo não exige alteração no núcleo.
    """
    from sklearn.ensemble import RandomForestClassifier

    classifier = train_persona_classifier(RandomForestClassifier(n_estimators=10, random_state=42))

    assert classifier.feature_columns == FEATURE_COLUMNS
    assert predict_persona(classifier, _sample_features()).value in {
        str(label) for label in classifier.label_encoder.classes_
    }


def test_predict_persona_preserves_training_column_order() -> None:
    """A ordem das colunas do treino é reproduzida na predição.

    Features embaralhadas no dicionário devem produzir a mesma predição que
    as mesmas features em ordem, porque o núcleo reordena antes de escalar.
    """
    classifier = knn.train_classifier()
    features = _sample_features()
    shuffled = dict(reversed(list(features.items())))

    assert predict_persona(classifier, features) == predict_persona(classifier, shuffled)


def test_predict_persona_rejects_missing_feature() -> None:
    """Feature faltante falha explicitamente em vez de prever com dado incompleto."""
    classifier = knn.train_classifier()
    features = _sample_features()
    del features["fail_rate"]

    with pytest.raises(ValueError, match="fail_rate"):
        predict_persona(classifier, features)


def test_predict_persona_rejects_unknown_feature() -> None:
    """Feature não reconhecida falha explicitamente, evitando ordem incorreta."""
    classifier = knn.train_classifier()
    features = _sample_features()
    features["true_persona"] = "Killer"

    with pytest.raises(ValueError, match="true_persona"):
        predict_persona(classifier, features)
