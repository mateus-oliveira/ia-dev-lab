"""Módulo de segurança, criptografia de senhas e autenticação JWT.

Implementa hashing com bcrypt, emissão e validação de tokens JWT (HS256)
e a dependência FastAPI para proteção de rotas restritas via Bearer Token.
"""

import os
import sqlite3
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from player_modeling.api.database import get_db

DEFAULT_SECRET_KEY = "change-this-in-production-use-a-strong-secret-key-32-chars"
DEFAULT_ALGORITHM = "HS256"
DEFAULT_EXPIRE_MINUTES = 30

security_scheme = HTTPBearer(auto_error=False)


def get_secret_key() -> str:
    """Retorna a chave secreta usada para assinar os tokens JWT.

    :return: String com o segredo configurado.
    """
    return os.getenv("JWT_SECRET_KEY", DEFAULT_SECRET_KEY)


def get_algorithm() -> str:
    """Retorna o algoritmo de assinatura do JWT.

    :return: String com o algoritmo (padrão: HS256).
    """
    return os.getenv("JWT_ALGORITHM", DEFAULT_ALGORITHM)


def get_access_token_expire_minutes() -> int:
    """Retorna o tempo de expiração em minutos do token JWT.

    :return: Inteiro representando os minutos de validade do token.
    """
    val = os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    if val is not None:
        try:
            return int(val)
        except ValueError:
            return DEFAULT_EXPIRE_MINUTES
    return DEFAULT_EXPIRE_MINUTES


def hash_password(password: str) -> str:
    """Gera um hash criptográfico seguro para a senha utilizando bcrypt.

    :param password: Senha em texto plano.
    :return: Hash bcrypt da senha em formato string UTF-8.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto plano coincide com o hash bcrypt armazenado.

    :param plain_password: Senha em texto plano a ser verificada.
    :param hashed_password: Hash bcrypt armazenado no banco de dados.
    :return: True se a senha for válida, False caso contrário.
    """
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Gera e assina um novo token JWT com os dados fornecidos e timestamp de expiração.

    :param data: Dicionário contendo as claims a serem incluídas no payload (ex: sub).
    :param expires_delta: Delta de tempo customizado para expiração do token.
    :return: Token JWT assinado em formato string.
    """
    to_encode = data.copy()
    now = datetime.now(UTC)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=get_access_token_expire_minutes())

    to_encode.update({"exp": expire, "iat": now})
    secret = get_secret_key()
    algorithm = get_algorithm()
    encoded_jwt: str = jwt.encode(to_encode, secret, algorithm=algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodifica e valida a assinatura e expiração de um token JWT.

    :param token: Token JWT em string.
    :return: Dicionário com as claims do payload decodificado.
    :raises jwt.ExpiredSignatureError: Se o token estiver expirado.
    :raises jwt.PyJWTError: Se o token for inválido, malformado ou assinatura incorreta.
    """
    secret = get_secret_key()
    algorithm = get_algorithm()
    payload = jwt.decode(token, secret, algorithms=[algorithm])
    return dict(payload)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)] = None,
    db: Annotated[sqlite3.Connection, Depends(get_db)] = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """Dependência de segurança reutilizável para interceptar requisições em rotas protegidas.

    Valida a presença, integridade, assinatura e expiração do Bearer Token JWT.
    Injeta o dicionário com os dados do usuário autenticado no contexto do endpoint.

    :param credentials: Credenciais Bearer extraídas do cabeçalho Authorization.
    :param db: Conexão ativa com o banco SQLite.
    :return: Dicionário com id, name e username do usuário autenticado.
    :raises HTTPException: 401 se o token for ausente, inválido, expirado ou usuário inexistente.
    """
    unauthorized_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais de autenticação inválidas ou ausentes",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.scheme.lower() != "bearer":
        raise unauthorized_exception

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação inválido",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    username: str | None = payload.get("sub")
    if not username:
        raise unauthorized_exception

    cursor = db.cursor()
    cursor.execute("SELECT id, name, username FROM users WHERE username = ?;", (username,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"id": row["id"], "name": row["name"], "username": row["username"]}
