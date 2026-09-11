"""Montagem do lote de eventos publicado pelo simulador na fila RabbitMQ."""

import random
import uuid
from datetime import datetime
from typing import Any

from player_modeling.simulator.events import (
    PERSONA_PROFILES,
    PERSONAS,
    generate_events,
    session_weights,
)

MIN_BATCH_EVENTS = 15
MAX_BATCH_EVENTS = 20


def build_player_batch(
    player_id: str | None = None,
    persona: str | None = None,
    start_time: datetime | None = None,
) -> dict[str, Any]:
    """Monta um lote de eventos recentes de um jogador simulado.

    :param player_id: identificador do jogador simulado; gerado
        automaticamente (sintético) se omitido.
    :param persona: persona da Taxonomia de Bartle usada para moldar a
        distribuição de tipos de evento e o tempo de decisão; sorteada
        automaticamente se omitida.
    :param start_time: instante inicial a partir do qual os timestamps dos
        eventos do lote avançam; usa o instante atual se omitido.

    :return: mensagem no formato publicado na fila: `player_id`,
        `session_id` e uma lista de 15 a 20 eventos recentes, cada um no
        formato de uma linha de `src/data/events.csv`. Nunca inclui a
        persona/`true_persona` do jogador simulado -- isso é o que o
        modelo de ML vai prever a partir dos eventos, não um dado
        publicado na fila.
    """
    persona = persona or random.choice(PERSONAS)
    player_id = player_id or f"player_{uuid.uuid4().hex[:8]}"
    session_id = str(uuid.uuid4())
    start_time = start_time or datetime.now()

    weights_dict = session_weights(persona)
    n_events = random.randint(MIN_BATCH_EVENTS, MAX_BATCH_EVENTS)
    events = generate_events(
        weights_dict,
        PERSONA_PROFILES[persona]["decision_time_ms"],
        session_id,
        player_id,
        n_events,
        start_time,
    )
    return {"player_id": player_id, "session_id": session_id, "events": events}
