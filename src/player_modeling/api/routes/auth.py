"""Rotas de autenticação (registro de usuários e login com JWT)."""

import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from player_modeling.api.database import get_db
from player_modeling.api.schemas import (
    LoginRequest,
    TokenResponse,
    UserRegisterRequest,
    UserResponse,
)
from player_modeling.api.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo usuário",
    description="Cadastra um novo usuário no banco SQLite com senha criptografada (bcrypt).",
)
def register(
    user_in: UserRegisterRequest,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
) -> UserResponse:
    """Registra um novo usuário na tabela users conforme a ADR 0004.

    :param user_in: Dados de registro validados pelo schema UserRegisterRequest.
    :param db: Conexão com o banco de dados injetada via FastAPI.
    :return: UserResponse contendo id, name e username cadastrados.
    :raises HTTPException: 409 Conflict se o username já existir.
    """
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?;", (user_in.username,))
    existing = cursor.fetchone()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O username '{user_in.username}' já está em uso.",
        )

    hashed_pwd = hash_password(user_in.password)
    cursor.execute(
        "INSERT INTO users (name, username, password) VALUES (?, ?, ?);",
        (user_in.name, user_in.username, hashed_pwd),
    )
    db.commit()
    user_id = cursor.lastrowid
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao persistir novo usuário.",
        )

    return UserResponse(id=user_id, name=user_in.name, username=user_in.username)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Autenticar usuário e emitir JWT",
    description="Valida credenciais e retorna Bearer Token JWT para rotas restritas.",
)
def login(
    login_in: LoginRequest,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
) -> TokenResponse:
    """Valida credenciais do usuário e emite um JSON Web Token (JWT).

    :param login_in: Credenciais de login (username e password).
    :param db: Conexão com o banco de dados injetada via FastAPI.
    :return: TokenResponse contendo o access_token assinado e tipo bearer.
    :raises HTTPException: 401 Unauthorized se as credenciais forem inválidas.
    """
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, name, username, password FROM users WHERE username = ?;",
        (login_in.username,),
    )
    user = cursor.fetchone()

    invalid_cred_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas: username ou senha incorretos.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if user is None:
        raise invalid_cred_exception

    if not verify_password(login_in.password, user["password"]):
        raise invalid_cred_exception

    access_token = create_access_token(data={"sub": user["username"], "user_id": user["id"]})
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter dados do usuário autenticado",
    description="Rota protegida que valida o Bearer Token e retorna dados do usuário autenticado.",
)
def get_me(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> UserResponse:
    """Retorna os dados do usuário autenticado a partir do token Bearer.

    :param current_user: Dicionário do usuário injetado pela dependência get_current_user.
    :return: UserResponse com id, name e username.
    """
    return UserResponse(
        id=int(current_user["id"]),
        name=str(current_user["name"]),
        username=str(current_user["username"]),
    )
