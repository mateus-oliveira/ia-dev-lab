"""Testes do ciclo de vida da aplicação FastAPI (treino dos classificadores no startup)."""

from fastapi.testclient import TestClient

from player_modeling.api.app import app
from player_modeling.ml import decision_tree, knn
from player_modeling.ml.knn import FEATURE_COLUMNS


def test_classifiers_are_trained_on_startup() -> None:
    """Subir a aplicação deixa todos os modelos treinados disponíveis em `app.state`."""
    with TestClient(app):
        classifiers = app.state.persona_classifiers

        assert set(classifiers) == {knn.MODEL_KEY, decision_tree.MODEL_KEY}
        for classifier in classifiers.values():
            assert classifier.feature_columns == FEATURE_COLUMNS
            assert classifier.model.n_features_in_ == len(FEATURE_COLUMNS)


def test_health_check_remains_public() -> None:
    """O endpoint de saúde continua acessível sem autenticação."""
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
