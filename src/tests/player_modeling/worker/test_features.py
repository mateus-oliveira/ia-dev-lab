"""Testes unitários da agregação de eventos em features (worker)."""

from typing import Any

from player_modeling.worker.features import extract_features


def _make_event(event_type: str, decision_time_ms: int, outcome: str = "success") -> dict[str, Any]:
    return {
        "event_id": "evt-1",
        "session_id": "session-1",
        "player_id": "player_test",
        "timestamp": "2026-01-01T00:00:00",
        "event_type": event_type,
        "decision_time_ms": decision_time_ms,
        "outcome": outcome,
    }


def test_extract_features_computes_expected_proportions() -> None:
    """Calcula corretamente as proporções e médias a partir de um lote de eventos."""
    events = [
        _make_event("attack", 100, "success"),
        _make_event("attack", 200, "fail"),
        _make_event("explore_area", 300, "success"),
        _make_event("chat", 400, "success"),
        _make_event("trade", 500, "fail"),
    ]

    features = extract_features("session-1", "player_test", events)

    assert features["session_id"] == "session-1"
    assert features["player_id"] == "player_test"
    assert features["n_events"] == 5
    assert features["pct_attack"] == 0.4
    assert features["pct_explore"] == 0.2
    assert features["pct_social"] == 0.4
    assert features["pct_quest_complete"] == 0.0
    assert features["pct_retry"] == 0.0
    assert features["avg_decision_time_ms"] == 300.0
    assert features["fail_rate"] == 0.4


def test_extract_features_never_includes_persona() -> None:
    """A linha de features nunca contém persona ou true_persona."""
    events = [_make_event("move", 150)]
    features = extract_features("session-2", "player_test", events)

    assert "persona" not in features
    assert "true_persona" not in features
