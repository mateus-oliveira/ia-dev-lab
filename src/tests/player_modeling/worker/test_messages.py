"""Testes unitários da validação/parsing das mensagens consumidas da fila."""

import json

import pytest

from player_modeling.worker.messages import InvalidMessageError, parse_message


def _valid_event() -> dict[str, object]:
    return {
        "event_id": "evt-1",
        "session_id": "session-1",
        "player_id": "player_test",
        "timestamp": "2026-01-01T00:00:00",
        "event_type": "attack",
        "decision_time_ms": 500,
        "outcome": "success",
    }


def test_parse_message_accepts_valid_payload() -> None:
    """Uma mensagem válida é parseada com os três campos esperados."""
    body = json.dumps(
        {"player_id": "player_test", "session_id": "session-1", "events": [_valid_event()]}
    ).encode("utf-8")

    message = parse_message(body)

    assert message["player_id"] == "player_test"
    assert message["session_id"] == "session-1"
    assert message["events"] == [_valid_event()]


def test_parse_message_rejects_invalid_json() -> None:
    """Corpo que não é JSON válido é rejeitado."""
    with pytest.raises(InvalidMessageError):
        parse_message(b"not-json")


def test_parse_message_rejects_missing_top_level_fields() -> None:
    """Mensagem sem player_id/session_id/events é rejeitada."""
    body = json.dumps({"player_id": "player_test"}).encode("utf-8")
    with pytest.raises(InvalidMessageError):
        parse_message(body)


def test_parse_message_rejects_empty_events_list() -> None:
    """Mensagem com lista de eventos vazia é rejeitada."""
    body = json.dumps({"player_id": "player_test", "session_id": "session-1", "events": []}).encode(
        "utf-8"
    )
    with pytest.raises(InvalidMessageError):
        parse_message(body)


def test_parse_message_rejects_event_missing_required_field() -> None:
    """Evento sem um campo obrigatório é rejeitado."""
    incomplete_event = _valid_event()
    del incomplete_event["decision_time_ms"]
    body = json.dumps(
        {"player_id": "player_test", "session_id": "session-1", "events": [incomplete_event]}
    ).encode("utf-8")
    with pytest.raises(InvalidMessageError):
        parse_message(body)
