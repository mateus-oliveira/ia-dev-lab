"""Testes de integração do endpoint GET /players/me/persona (inferência real com KNN)."""

import sqlite3
from collections.abc import Callable, Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from starlette.requests import Request

from player_modeling.api.app import app
from player_modeling.api.database import get_connection, get_db
from player_modeling.api.routes.players import get_persona_classifier
from player_modeling.api.schemas import BartlePersona
from player_modeling.api.security import create_access_token, hash_password
from player_modeling.ml.knn import PersonaClassifier, predict_persona, train_classifier

PLAYER_ONE = "player_0000"
PLAYER_TWO = "player_0001"

AGGRESSIVE_FEATURES: dict[str, Any] = {
    "n_events": 60,
    "pct_attack": 0.45,
    "pct_explore": 0.03,
    "pct_social": 0.02,
    "pct_quest_complete": 0.08,
    "pct_retry": 0.05,
    "avg_decision_time_ms": 450.0,
    "fail_rate": 0.2,
}

SOCIABLE_FEATURES: dict[str, Any] = {
    "n_events": 60,
    "pct_attack": 0.03,
    "pct_explore": 0.05,
    "pct_social": 0.5,
    "pct_quest_complete": 0.05,
    "pct_retry": 0.04,
    "avg_decision_time_ms": 900.0,
    "fail_rate": 0.1,
}


@pytest.fixture(scope="module")
def classifier() -> PersonaClassifier:
    """Treina um classificador de referência para comparar com a resposta da API.

    :return: artefatos treinados com o dataset sintético do repositório.
    """
    return train_classifier()


def _insert_user(connection: sqlite3.Connection, username: str) -> None:
    """Registra um usuário de teste na tabela `users`.

    :param connection: Conexão SQLite aberta.
    :param username: Username do jogador, usado também como `player_id`.
    """
    connection.execute(
        "INSERT INTO users (name, username, password) VALUES (?, ?, ?);",
        (f"Jogador {username}", username, hash_password("pass123")),
    )
    connection.commit()


def _insert_features(
    connection: sqlite3.Connection,
    player_id: str,
    features: dict[str, Any],
    session_id: str = "session-1",
) -> None:
    """Persiste uma linha de features de um jogador, como faria o worker subscriber.

    :param connection: Conexão SQLite aberta.
    :param player_id: Identificador do jogador dono das features.
    :param features: Features agregadas do lote.
    :param session_id: Identificador da sessão/lote.
    """
    connection.execute(
        """
        INSERT INTO player_features (
            player_id, session_id, n_events, pct_attack, pct_explore,
            pct_social, pct_quest_complete, pct_retry,
            avg_decision_time_ms, fail_rate, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            player_id,
            session_id,
            features["n_events"],
            features["pct_attack"],
            features["pct_explore"],
            features["pct_social"],
            features["pct_quest_complete"],
            features["pct_retry"],
            features["avg_decision_time_ms"],
            features["fail_rate"],
            datetime.now(UTC).isoformat(),
        ),
    )
    connection.commit()


@pytest.fixture
def db_file(tmp_path: Path, apply_migrations: Callable[[str], None]) -> str:
    """Cria um banco SQLite isolado e migrado com os dois jogadores de teste.

    :param tmp_path: Diretório temporário fornecido pelo pytest.
    :param apply_migrations: Fixture que aplica `alembic upgrade head`.

    :return: Caminho do banco de teste.
    """
    path = str(tmp_path / "test_persona.sqlite3")
    apply_migrations(path)

    connection = get_connection(path)
    try:
        _insert_user(connection, PLAYER_ONE)
        _insert_user(connection, PLAYER_TWO)
    finally:
        connection.close()

    return path


@pytest.fixture
def client(db_file: str) -> Generator[TestClient, None, None]:
    """Cliente HTTP apontando para o banco de teste isolado.

    :param db_file: Caminho do banco de teste já migrado e populado.

    :return: Gerador do cliente de teste.
    """

    def override_get_db() -> Generator[sqlite3.Connection, None, None]:
        connection = get_connection(db_file)
        try:
            yield connection
        finally:
            connection.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _auth_headers(username: str) -> dict[str, str]:
    """Monta o cabeçalho Authorization de um jogador.

    :param username: Username do jogador autenticado.

    :return: Cabeçalho com Bearer Token JWT válido.
    """
    return {"Authorization": f"Bearer {create_access_token({'sub': username})}"}


def test_get_persona_success(
    client: TestClient, db_file: str, classifier: PersonaClassifier
) -> None:
    """Consulta autenticada devolve a persona prevista para o próprio jogador.

    :param client: Cliente HTTP de teste.
    :param db_file: Caminho do banco de teste.
    :param classifier: Classificador de referência treinado na fixture.
    """
    connection = get_connection(db_file)
    try:
        _insert_features(connection, PLAYER_ONE, AGGRESSIVE_FEATURES)
    finally:
        connection.close()

    response = client.get("/players/me/persona", headers=_auth_headers(PLAYER_ONE))

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["player_id"] == PLAYER_ONE
    assert data["persona"] in [persona.value for persona in BartlePersona]
    assert data["persona"] == predict_persona(classifier, AGGRESSIVE_FEATURES).value


def test_get_persona_uses_latest_features(
    client: TestClient, db_file: str, classifier: PersonaClassifier
) -> None:
    """Com histórico, a predição usa a linha mais recente e o perfil evolui.

    :param client: Cliente HTTP de teste.
    :param db_file: Caminho do banco de teste.
    :param classifier: Classificador de referência treinado na fixture.
    """
    connection = get_connection(db_file)
    try:
        _insert_features(connection, PLAYER_ONE, AGGRESSIVE_FEATURES, session_id="session-1")
    finally:
        connection.close()

    first_response = client.get("/players/me/persona", headers=_auth_headers(PLAYER_ONE))

    connection = get_connection(db_file)
    try:
        _insert_features(connection, PLAYER_ONE, SOCIABLE_FEATURES, session_id="session-2")
    finally:
        connection.close()

    second_response = client.get("/players/me/persona", headers=_auth_headers(PLAYER_ONE))

    assert (
        first_response.json()["persona"] == predict_persona(classifier, AGGRESSIVE_FEATURES).value
    )
    assert second_response.json()["persona"] == predict_persona(classifier, SOCIABLE_FEATURES).value
    assert first_response.json()["persona"] != second_response.json()["persona"]


def test_get_persona_isolates_players(
    client: TestClient, db_file: str, classifier: PersonaClassifier
) -> None:
    """Cada token recebe a predição das features do seu próprio jogador.

    :param client: Cliente HTTP de teste.
    :param db_file: Caminho do banco de teste.
    :param classifier: Classificador de referência treinado na fixture.
    """
    connection = get_connection(db_file)
    try:
        _insert_features(connection, PLAYER_ONE, AGGRESSIVE_FEATURES)
        _insert_features(connection, PLAYER_TWO, SOCIABLE_FEATURES)
    finally:
        connection.close()

    first = client.get("/players/me/persona", headers=_auth_headers(PLAYER_ONE)).json()
    second = client.get("/players/me/persona", headers=_auth_headers(PLAYER_TWO)).json()

    assert first["player_id"] == PLAYER_ONE
    assert second["player_id"] == PLAYER_TWO
    assert first["persona"] == predict_persona(classifier, AGGRESSIVE_FEATURES).value
    assert second["persona"] == predict_persona(classifier, SOCIABLE_FEATURES).value


def test_get_persona_without_features_returns_404(client: TestClient) -> None:
    """Jogador sem features registradas recebe 404 em vez de persona inventada.

    :param client: Cliente HTTP de teste.
    """
    response = client.get("/players/me/persona", headers=_auth_headers(PLAYER_ONE))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert PLAYER_ONE in response.json()["detail"]


def test_get_persona_without_token(client: TestClient) -> None:
    """Requisição sem autenticação é rejeitada com 401.

    :param client: Cliente HTTP de teste.
    """
    response = client.get("/players/me/persona")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_persona_invalid_token(client: TestClient) -> None:
    """Token malformado é rejeitado com 401.

    :param client: Cliente HTTP de teste.
    """
    response = client.get(
        "/players/me/persona", headers={"Authorization": "Bearer token.completamente.invalido"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_persona_expired_token(client: TestClient) -> None:
    """Token expirado é rejeitado com 401.

    :param client: Cliente HTTP de teste.
    """
    token = create_access_token({"sub": PLAYER_ONE}, expires_delta=timedelta(seconds=-30))

    response = client.get("/players/me/persona", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expirado" in response.json()["detail"]


def test_persona_route_no_longer_accepts_player_id(client: TestClient) -> None:
    """A rota antiga com `player_id` no path não existe mais.

    :param client: Cliente HTTP de teste.
    """
    response = client.get(f"/players/{PLAYER_TWO}/persona", headers=_auth_headers(PLAYER_ONE))

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_classifier_is_reused_between_requests(client: TestClient, db_file: str) -> None:
    """O mesmo classificador treinado atende requisições sucessivas.

    :param client: Cliente HTTP de teste.
    :param db_file: Caminho do banco de teste.
    """
    connection = get_connection(db_file)
    try:
        _insert_features(connection, PLAYER_ONE, AGGRESSIVE_FEATURES)
    finally:
        connection.close()

    used: list[PersonaClassifier] = []

    def spy_get_persona_classifier(request: Request) -> PersonaClassifier:
        classifier = get_persona_classifier(request)
        used.append(classifier)
        return classifier

    app.dependency_overrides[get_persona_classifier] = spy_get_persona_classifier
    try:
        headers = _auth_headers(PLAYER_ONE)
        client.get("/players/me/persona", headers=headers)
        client.get("/players/me/persona", headers=headers)
    finally:
        app.dependency_overrides.pop(get_persona_classifier)

    assert len(used) == 2
    assert used[0] is used[1]
