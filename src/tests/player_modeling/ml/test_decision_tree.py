"""Testes do classificador DecisionTree de personas (treino, predição e avaliação)."""

from pathlib import Path
from typing import Any

import pytest
from sklearn.tree import DecisionTreeClassifier

from player_modeling.api.schemas import BartlePersona
from player_modeling.ml.decision_tree import (
    FEATURE_COLUMNS,
    MAX_DEPTH,
    MODEL_KEY,
    PersonaClassifier,
    build_estimator,
    evaluate_classifier,
    load_dataset,
    predict_persona,
    train_classifier,
)

MIN_EXPECTED_ACCURACY = 0.85


@pytest.fixture(scope="module")
def classifier() -> PersonaClassifier:
    """Treina a árvore uma única vez para todos os testes do módulo.

    :return: artefatos treinados com o dataset sintético do repositório.
    """
    return train_classifier()


def _sample_features() -> dict[str, Any]:
    """Monta um conjunto de features válido no formato da pipeline.

    :return: dicionário com exatamente as features esperadas pelo classificador.
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


def test_model_key_identifies_the_model_in_the_api_contract() -> None:
    """A chave do modelo é o nome usado no contrato da API e no script de avaliação."""
    assert MODEL_KEY == "decision_tree"


def test_build_estimator_returns_bounded_decision_tree() -> None:
    """O estimador é uma árvore de decisão com profundidade limitada e semente fixa."""
    estimator = build_estimator()

    assert isinstance(estimator, DecisionTreeClassifier)
    assert estimator.max_depth == MAX_DEPTH
    assert estimator.random_state is not None


def test_build_estimator_returns_a_new_instance_each_call() -> None:
    """Cada chamada devolve uma instância limpa, para não reaproveitar estado ajustado."""
    assert build_estimator() is not build_estimator()


def test_train_classifier_returns_fitted_artifacts(classifier: PersonaClassifier) -> None:
    """O treino devolve artefatos ajustados e a ordem de features usada.

    :param classifier: Classificador treinado pela fixture do módulo.
    """
    assert classifier.feature_columns == FEATURE_COLUMNS
    assert classifier.scaler.n_features_in_ == len(FEATURE_COLUMNS)
    assert classifier.model.n_features_in_ == len(FEATURE_COLUMNS)


def test_train_classifier_learns_only_bartle_labels(classifier: PersonaClassifier) -> None:
    """As classes aprendidas são exatamente os quatro perfis da Taxonomia de Bartle.

    :param classifier: Classificador treinado pela fixture do módulo.
    """
    learned = {str(label) for label in classifier.label_encoder.classes_}
    assert learned == {persona.value for persona in BartlePersona}


def test_trained_tree_respects_max_depth(classifier: PersonaClassifier) -> None:
    """A árvore treinada não ultrapassa a profundidade máxima configurada.

    :param classifier: Classificador treinado pela fixture do módulo.
    """
    assert classifier.model.get_depth() <= MAX_DEPTH


def test_predict_persona_returns_bartle_persona(classifier: PersonaClassifier) -> None:
    """A predição devolve um membro do Enum BartlePersona.

    :param classifier: Classificador treinado pela fixture do módulo.
    """
    assert isinstance(predict_persona(classifier, _sample_features()), BartlePersona)


def test_predict_persona_is_deterministic(classifier: PersonaClassifier) -> None:
    """Duas predições sobre as mesmas features devolvem o mesmo perfil.

    :param classifier: Classificador treinado pela fixture do módulo.
    """
    features = _sample_features()

    assert predict_persona(classifier, features) == predict_persona(classifier, features)


def test_predict_persona_reacts_to_different_behaviours(classifier: PersonaClassifier) -> None:
    """Features de comportamentos distintos produzem perfis distintos.

    :param classifier: Classificador treinado pela fixture do módulo.
    """
    aggressive = {
        "n_events": 60,
        "pct_attack": 0.45,
        "pct_explore": 0.03,
        "pct_social": 0.02,
        "pct_quest_complete": 0.08,
        "pct_retry": 0.05,
        "avg_decision_time_ms": 450.0,
        "fail_rate": 0.2,
    }
    sociable = {
        "n_events": 60,
        "pct_attack": 0.03,
        "pct_explore": 0.05,
        "pct_social": 0.5,
        "pct_quest_complete": 0.05,
        "pct_retry": 0.04,
        "avg_decision_time_ms": 900.0,
        "fail_rate": 0.1,
    }

    assert predict_persona(classifier, aggressive) != predict_persona(classifier, sociable)


def test_predict_persona_rejects_missing_feature(classifier: PersonaClassifier) -> None:
    """Feature faltante falha explicitamente em vez de prever com dado incompleto.

    :param classifier: Classificador treinado pela fixture do módulo.
    """
    features = _sample_features()
    del features["fail_rate"]

    with pytest.raises(ValueError, match="fail_rate"):
        predict_persona(classifier, features)


def test_predict_persona_rejects_unknown_feature(classifier: PersonaClassifier) -> None:
    """Feature não reconhecida falha explicitamente, evitando ordem incorreta.

    :param classifier: Classificador treinado pela fixture do módulo.
    """
    features = _sample_features()
    features["true_persona"] = "Killer"

    with pytest.raises(ValueError, match="true_persona"):
        predict_persona(classifier, features)


def test_evaluate_classifier_reports_accuracy_above_threshold() -> None:
    """A avaliação devolve acurácia válida e acima do mínimo esperado."""
    evaluation = evaluate_classifier()

    assert 0.0 <= evaluation.accuracy <= 1.0
    assert evaluation.accuracy >= MIN_EXPECTED_ACCURACY
    assert evaluation.classes == tuple(sorted(persona.value for persona in BartlePersona))
    for persona in BartlePersona:
        assert persona.value in evaluation.report


def test_load_dataset_missing_file_raises(tmp_path: Path) -> None:
    """Dataset inexistente falha explicitamente em vez de treinar vazio.

    :param tmp_path: Diretório temporário fornecido pelo pytest.
    """
    with pytest.raises(FileNotFoundError):
        load_dataset(tmp_path / "inexistente.csv")
