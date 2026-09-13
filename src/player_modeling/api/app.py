"""Ponto de entrada da aplicação FastAPI para o Player Modeling Lab."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from player_modeling.api.routes.auth import router as auth_router
from player_modeling.api.routes.players import router as players_router
from player_modeling.api.security import get_secret_key
from player_modeling.ml import decision_tree, knn


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Gerenciador de ciclo de vida da aplicação FastAPI.

    Treina os classificadores de personas uma única vez na subida do
    servidor e os mantém em `app.state.persona_classifiers`, indexados pela
    chave de cada modelo, para todas as requisições (ADR 0010). Um dataset
    ausente ou inválido interrompe a inicialização, em vez de falhar
    requisição por requisição.

    Valida também, antes de qualquer coisa, que o segredo de assinatura
    dos tokens JWT está configurado (ADR 0012): a aplicação não deve subir
    assinando tokens com um segredo ausente ou fraco.

    O schema do banco é responsabilidade exclusiva das migrações Alembic
    (`alembic upgrade head`), não da inicialização da API.

    :param app: Instância da aplicação FastAPI.
    :return: Gerador assíncrono de contexto.
    """
    get_secret_key()
    app.state.persona_classifiers = {
        knn.MODEL_KEY: knn.train_classifier(),
        decision_tree.MODEL_KEY: decision_tree.train_classifier(),
    }
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

    return app


app = create_app()
