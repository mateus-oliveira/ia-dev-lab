"""Rotas de jogadores e consulta de perfil na Taxonomia de Bartle."""

import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from player_modeling.api.database import get_db
from player_modeling.api.schemas import PersonaResponse
from player_modeling.api.security import get_current_user
from player_modeling.ml.knn import FEATURE_COLUMNS, PersonaClassifier, predict_persona

router = APIRouter(prefix="/players", tags=["Jogadores"])

LATEST_FEATURES_QUERY = f"""
    SELECT {", ".join(FEATURE_COLUMNS)}
    FROM player_features
    WHERE player_id = ?
    ORDER BY id DESC
    LIMIT 1
"""


def get_persona_classifier(request: Request) -> PersonaClassifier:
    """Recupera o classificador treinado na inicialização da aplicação.

    :param request: Requisição atual, usada para acessar `app.state`.
    :return: Artefatos treinados compartilhados por todas as requisições.
    """
    classifier: PersonaClassifier = request.app.state.persona_classifier
    return classifier


def get_latest_player_features(
    connection: sqlite3.Connection, player_id: str
) -> dict[str, Any] | None:
    """Busca as features agregadas mais recentes de um jogador.

    Ordena por `id` decrescente, aproveitando o índice composto
    `(player_id, id)` de `player_features` (ADR 0008): `id` é
    autoincremental, portanto identifica a última mensagem processada sem
    depender do desempate de `created_at`.

    :param connection: Conexão SQLite aberta.
    :param player_id: Identificador do jogador (igual ao `username`).

    :return: Dicionário com as features esperadas pelo classificador, ou
        `None` se o jogador ainda não tiver nenhuma linha registrada.
    """
    row = connection.execute(LATEST_FEATURES_QUERY, (player_id,)).fetchone()
    if row is None:
        return None
    return {column: row[column] for column in FEATURE_COLUMNS}


@router.get(
    "/me/persona",
    response_model=PersonaResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar persona do jogador autenticado",
    description=(
        "Retorna o perfil do jogador autenticado na Taxonomia de Bartle, previsto por "
        "um classificador KNN a partir das features mais recentes registradas pela "
        "pipeline (simulador -> RabbitMQ -> worker) para esse jogador."
    ),
)
def get_my_persona(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    classifier: Annotated[PersonaClassifier, Depends(get_persona_classifier)],
    db: Annotated[sqlite3.Connection, Depends(get_db)],
) -> PersonaResponse:
    """Prevê a persona do jogador autenticado a partir de suas features mais recentes.

    O jogador consultado é sempre o dono do Bearer Token JWT: não há
    parâmetro de jogador na requisição (ADR 0010).

    :param current_user: Usuário autenticado injetado por dependência.
    :param classifier: Classificador treinado na inicialização da API.
    :param db: Conexão ativa com o banco SQLite.

    :return: PersonaResponse com o `player_id` autenticado e a persona prevista.
    :raises HTTPException: 404 se o jogador ainda não possuir features registradas.
    """
    player_id = str(current_user["username"])
    features = get_latest_player_features(db, player_id)
    if features is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Nenhuma feature registrada para o jogador '{player_id}': "
                "a pipeline ainda não processou eventos desse jogador."
            ),
        )

    persona = predict_persona(classifier, features)
    return PersonaResponse(player_id=player_id, persona=persona)
