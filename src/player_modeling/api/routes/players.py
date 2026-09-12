"""Rotas de jogadores e consulta de perfil na Taxonomia de Bartle."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, status

from player_modeling.api.schemas import BartlePersona, PersonaResponse
from player_modeling.api.security import get_current_user

router = APIRouter(prefix="/players", tags=["Jogadores"])

_BARTLE_PERSONAS = [
    BartlePersona.KILLER,
    BartlePersona.ACHIEVER,
    BartlePersona.SOCIALIZER,
    BartlePersona.EXPLORER,
]


def resolve_mock_persona(player_id: str) -> BartlePersona:
    """Calcula deterministiamente a persona mockada para um jogador a partir do seu ID.

    :param player_id: Identificador do jogador (ex: player_0000).
    :return: Arquétipo sorteado de forma determinística na Taxonomia de Bartle.
    """
    index = sum(ord(c) for c in player_id) % len(_BARTLE_PERSONAS)
    return _BARTLE_PERSONAS[index]


@router.get(
    "/{player_id}/persona",
    response_model=PersonaResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar persona do jogador (Stub/Mock)",
    description=(
        "Retorna o perfil previsto do jogador segundo a Taxonomia de Bartle. "
        "Atualmente opera em modo stub/mock para validação imediata de contrato."
    ),
)
def get_player_persona(
    player_id: Annotated[
        str,
        Path(
            ...,
            pattern=r"^player_\d{4,}$",
            description="Identificador do jogador alinhado aos dados sintéticos (ex: player_0000)",
        ),
    ],
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> PersonaResponse:
    """Retorna o perfil mockado do jogador na Taxonomia de Bartle.

    Requer autenticação prévia via Bearer Token JWT.

    :param player_id: Identificador do jogador validado por regex.
    :param current_user: Contexto do usuário autenticado injetado por dependência.
    :return: PersonaResponse contendo player_id e a persona correspondente.
    """
    persona = resolve_mock_persona(player_id)
    return PersonaResponse(player_id=player_id, persona=persona)
