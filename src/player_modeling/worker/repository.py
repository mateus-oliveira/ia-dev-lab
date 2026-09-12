"""Persistência das features agregadas na tabela `player_features`."""

import sqlite3
from datetime import UTC, datetime
from typing import Any


def save_player_features(connection: sqlite3.Connection, features: dict[str, Any]) -> None:
    """Persiste uma linha de features agregadas em `player_features`.

    Usa uma conexão já aberta e reaproveitada pelo chamador (ver ADR
    0008): esta função não abre nem fecha a conexão.

    :param connection: conexão SQLite aberta (ver `api.database.get_connection`).
    :param features: dicionário retornado por
        `player_modeling.worker.features.extract_features`.
    """
    created_at = datetime.now(UTC).isoformat()
    connection.execute(
        """
        INSERT INTO player_features (
            player_id, session_id, n_events, pct_attack, pct_explore,
            pct_social, pct_quest_complete, pct_retry,
            avg_decision_time_ms, fail_rate, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            features["player_id"],
            features["session_id"],
            features["n_events"],
            features["pct_attack"],
            features["pct_explore"],
            features["pct_social"],
            features["pct_quest_complete"],
            features["pct_retry"],
            features["avg_decision_time_ms"],
            features["fail_rate"],
            created_at,
        ),
    )
    connection.commit()
