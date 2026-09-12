"""Validação e parsing das mensagens consumidas da fila de eventos."""

import json
from typing import Any

_REQUIRED_EVENT_FIELDS = (
    "event_id",
    "session_id",
    "player_id",
    "timestamp",
    "event_type",
    "decision_time_ms",
    "outcome",
)


class InvalidMessageError(ValueError):
    """Levantada quando uma mensagem consumida não tem o formato esperado."""


def parse_message(body: bytes) -> dict[str, Any]:
    """Decodifica e valida uma mensagem consumida da fila.

    O formato esperado é o contrato fixado pelo publisher: um objeto JSON
    com `player_id`, `session_id` e `events` (lista não vazia de eventos
    no formato de `src/data/events.csv`).

    :param body: corpo bruto (bytes) da mensagem AMQP.

    :return: dicionário com `player_id`, `session_id` e `events` validados.

    :raises InvalidMessageError: se a mensagem não puder ser decodificada
        como JSON, ou não contiver os campos/tipos esperados.
    """
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise InvalidMessageError(f"corpo da mensagem nao e JSON valido: {exc}") from exc

    if not isinstance(payload, dict):
        raise InvalidMessageError("mensagem deve ser um objeto JSON")

    player_id = payload.get("player_id")
    session_id = payload.get("session_id")
    events = payload.get("events")

    if not isinstance(player_id, str) or not player_id:
        raise InvalidMessageError("campo 'player_id' ausente ou invalido")
    if not isinstance(session_id, str) or not session_id:
        raise InvalidMessageError("campo 'session_id' ausente ou invalido")
    if not isinstance(events, list) or not events:
        raise InvalidMessageError("campo 'events' ausente, vazio ou invalido")

    for event in events:
        if not isinstance(event, dict):
            raise InvalidMessageError("cada evento deve ser um objeto JSON")
        missing = [field for field in _REQUIRED_EVENT_FIELDS if field not in event]
        if missing:
            raise InvalidMessageError(f"evento sem os campos obrigatorios: {missing}")

    return {"player_id": player_id, "session_id": session_id, "events": events}
