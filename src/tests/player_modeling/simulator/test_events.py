"""Testes unitários da geração de eventos sintéticos por persona."""

from datetime import datetime

from player_modeling.simulator.events import (
    EVENT_TYPES,
    PERSONAS,
    generate_events,
    session_weights,
)

EXPECTED_EVENT_KEYS = {
    "event_id",
    "session_id",
    "player_id",
    "timestamp",
    "event_type",
    "decision_time_ms",
    "outcome",
}


def test_session_weights_covers_all_event_types_and_sums_to_one() -> None:
    """Os pesos retornados cobrem todos os tipos de evento e somam ~1."""
    for persona in PERSONAS:
        weights = session_weights(persona)
        assert set(weights.keys()) == set(EVENT_TYPES)
        assert abs(sum(weights.values()) - 1.0) < 1e-9
        assert all(weight > 0 for weight in weights.values())


def test_generate_events_returns_requested_window_size() -> None:
    """Gera exatamente a quantidade de eventos pedida, no formato de events.csv."""
    weights = session_weights("Killer")
    n_events = 18

    events = generate_events(
        weights,
        (200, 800),
        session_id="session-1",
        player_id="player_test",
        n_events=n_events,
        start_time=datetime(2026, 1, 1),
    )

    assert len(events) == n_events
    event_ids = set()
    for event in events:
        assert set(event.keys()) == EXPECTED_EVENT_KEYS
        assert event["session_id"] == "session-1"
        assert event["player_id"] == "player_test"
        assert event["event_type"] in EVENT_TYPES
        assert event["outcome"] in {"success", "fail", "retry"}
        assert event["decision_time_ms"] >= 50
        event_ids.add(event["event_id"])

    assert len(event_ids) == n_events


def test_generate_events_timestamps_strictly_increase() -> None:
    """Os timestamps avançam estritamente ao longo do lote gerado."""
    weights = session_weights("Explorer")
    events = generate_events(
        weights, (550, 1600), "session-2", "player_test", 10, datetime(2026, 1, 1)
    )

    timestamps = [datetime.fromisoformat(event["timestamp"]) for event in events]
    assert timestamps == sorted(timestamps)
    assert len(set(timestamps)) == len(timestamps)
