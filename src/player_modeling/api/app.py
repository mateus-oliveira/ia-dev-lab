"""Ponto de entrada da aplicação FastAPI para o Player Modeling Lab."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI

from player_modeling.api.routes.auth import router as auth_router
from player_modeling.api.routes.players import router as players_router
from player_modeling.api.security import get_current_user
from player_modeling.ml.knn import train_classifier


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Gerenciador de ciclo de vida da aplicação FastAPI.

    Treina o classificador de personas uma única vez na subida do servidor
    e o mantém em `app.state.persona_classifier` para todas as requisições
    (ADR 0010). Um dataset ausente ou inválido interrompe a inicialização,
    em vez de falhar requisição por requisição.

    O schema do banco é responsabilidade exclusiva das migrações Alembic
    (`alembic upgrade head`), não da inicialização da API.

    :param app: Instância da aplicação FastAPI.
    :return: Gerador assíncrono de contexto.
    """
    app.state.persona_classifier = train_classifier()
    yield


def create_app() -> FastAPI:
    """Cria e configura a instância principal do FastAPI.

    :return: Instância configurada do FastAPI com rotas registradas.
    """
    app = FastAPI(
        title="Player Modeling API",
        description="API REST para modelagem de jogadores, predição e autenticação.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(auth_router)
    app.include_router(players_router)

    @app.get("/health", tags=["Monitoramento"])
    def health_check() -> dict[str, str]:
        """Endpoint público de verificação de integridade da API."""
        return {"status": "ok"}

    @app.get("/protected-sample", tags=["Exemplo"])
    def protected_sample(
        current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    ) -> dict[str, Any]:
        """Endpoint de exemplo para validação de rota restrita com Bearer Token."""
        return {
            "message": "Acesso autorizado com sucesso!",
            "user": current_user,
        }

    return app


app = create_app()
