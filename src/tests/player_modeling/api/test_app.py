"""Testes do ciclo de vida da aplicação FastAPI (treino do classificador no startup)."""

from fastapi.testclient import TestClient

from player_modeling.api.app import app
from player_modeling.ml.knn import FEATURE_COLUMNS, PersonaClassifier


def test_classifier_is_trained_on_startup() -> None:
    """Subir a aplicação deixa o classificador treinado disponível em `app.state`."""
    with TestClient(app):
        classifier = app.state.persona_classifier

        assert isinstance(classifier, PersonaClassifier)
        assert classifier.feature_columns == FEATURE_COLUMNS
        assert classifier.model.n_features_in_ == len(FEATURE_COLUMNS)


def test_health_check_remains_public() -> None:
    """O endpoint de saúde continua acessível sem autenticação."""
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
