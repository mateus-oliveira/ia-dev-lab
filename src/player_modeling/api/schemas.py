"""Schemas Pydantic para validação de dados da API de autenticação."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class BartlePersona(str, Enum):
    """Arquétipos de jogadores segundo a Taxonomia de Bartle."""

    KILLER = "Killer"
    ACHIEVER = "Achiever"
    SOCIALIZER = "Socializer"
    EXPLORER = "Explorer"


class PersonaResponse(BaseModel):
    """Schema para resposta da predição do perfil do jogador (Taxonomia de Bartle)."""

    model_config = ConfigDict(from_attributes=True)

    player_id: str = Field(
        ...,
        pattern=r"^player_\d{4,}$",
        description="Identificador do jogador",
    )
    persona: BartlePersona = Field(
        ...,
        description="Perfil previsto na Taxonomia de Bartle",
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
