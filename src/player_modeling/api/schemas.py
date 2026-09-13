"""Schemas Pydantic para validação de dados da API de autenticação.

`BartlePersona` é declarada em `player_modeling.domain.personas` — ela é
vocabulário do domínio, não da camada HTTP — e re-exportada aqui porque
compõe o contrato de resposta de `PersonaResponse`.
"""

from pydantic import BaseModel, ConfigDict, Field

from player_modeling.domain.personas import BartlePersona

__all__ = [
    "BartlePersona",
    "LoginRequest",
    "PersonaResponse",
    "TokenPayload",
    "TokenResponse",
    "UserRegisterRequest",
    "UserResponse",
]


class PersonaResponse(BaseModel):
    """Schema para resposta da predição do perfil do jogador (Taxonomia de Bartle).

    Há um campo por modelo servido pela API, nomeado pela chave do modelo
    (`MODEL_KEY` do módulo correspondente em `player_modeling.ml`), para que
    toda persona retornada seja rastreável ao classificador que a produziu.
    """

    model_config = ConfigDict(from_attributes=True)

    player_id: str = Field(
        ...,
        pattern=r"^player_\d{4,}$",
        description="Identificador do jogador",
    )
    knn: BartlePersona = Field(
        ...,
        description="Perfil previsto pelo classificador KNN",
    )
    decision_tree: BartlePersona = Field(
        ...,
        description="Perfil previsto pela Árvore de Decisão",
    )


class UserRegisterRequest(BaseModel):
    """Schema para requisição de cadastro de usuário (User Story 1 / ADR 0004)."""

    name: str = Field(..., min_length=1, max_length=255, description="Nome completo do jogador")
    username: str = Field(
        ...,
        pattern=r"^player_\d{4,}$",
        description="Identificador alinhado aos IDs de jogadores (ex: player_0000)",
    )
    password: str = Field(..., min_length=6, max_length=128, description="Senha do usuário")


class UserResponse(BaseModel):
    """Schema para resposta pública de dados do usuário, sem expor a senha."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    username: str


class LoginRequest(BaseModel):
    """Schema para requisição de login e autenticação (User Story 2)."""

    username: str = Field(..., min_length=1, description="Username do jogador")
    password: str = Field(..., min_length=1, description="Senha em texto plano para conferência")


class TokenResponse(BaseModel):
    """Schema para resposta de emissão de token JWT."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema para dados contidos no payload do token JWT decodificado."""

    sub: str | None = None
    exp: int | None = None
