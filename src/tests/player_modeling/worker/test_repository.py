"""Testes da persistência de features em `player_features` (SQLite real, migrado)."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from player_modeling.api.database import get_connection
from player_modeling.worker.repository import save_player_features


def _make_features(player_id: str = "player_test", session_id: str = "session-1") -> dict[str, Any]:
    return {
        "player_id": player_id,
        "session_id": session_id,
        "n_events": 18,
        "pct_attack": 0.2,
        "pct_explore": 0.1,
        "pct_social": 0.3,
        "pct_quest_complete": 0.2,
        "pct_retry": 0.1,
        "avg_decision_time_ms": 650.5,
        "fail_rate": 0.15,
    }


def test_save_player_features_inserts_row(
    tmp_path: Path, apply_migrations: Callable[[str], None]
) -> None:
    """Persiste uma linha em `player_features` com os valores esperados.

    :param tmp_path: Diretório temporário fornecido pelo pytest.
    :param apply_migrations: Fixture que aplica `alembic upgrade head` a um banco de teste.
    """
    db_file = str(tmp_path / "test_db.sqlite3")
    apply_migrations(db_file)

    connection = get_connection(db_file)
    try:
        save_player_features(connection, _make_features())

        row = connection.execute(
            "SELECT * FROM player_features WHERE player_id = ?", ("player_test",)
        ).fetchone()
        assert row is not None
        assert row["session_id"] == "session-1"
        assert row["n_events"] == 18
        assert row["pct_attack"] == 0.2
        assert row["created_at"]
    finally:
        connection.close()


def test_save_player_features_keeps_history_per_player(
    tmp_path: Path, apply_migrations: Callable[[str], None]
) -> None:
    """Duas mensagens do mesmo jogador geram duas linhas distintas (histórico).

    :param tmp_path: Diretório temporário fornecido pelo pytest.
    :param apply_migrations: Fixture que aplica `alembic upgrade head` a um banco de teste.
    """
    db_file = str(tmp_path / "test_db.sqlite3")
    apply_migrations(db_file)

    connection = get_connection(db_file)
    try:
        save_player_features(connection, _make_features(session_id="session-1"))
        save_player_features(connection, _make_features(session_id="session-2"))

        rows = connection.execute(
            "SELECT session_id FROM player_features WHERE player_id = ? ORDER BY id",
            ("player_test",),
        ).fetchall()
        assert [row["session_id"] for row in rows] == ["session-1", "session-2"]
    finally:
        connection.close()


def test_index_supports_latest_row_lookup(
    tmp_path: Path, apply_migrations: Callable[[str], None]
) -> None:
    """A consulta pela linha mais recente de um jogador retorna a última inserida.

    :param tmp_path: Diretório temporário fornecido pelo pytest.
    :param apply_migrations: Fixture que aplica `alembic upgrade head` a um banco de teste.
    """
    db_file = str(tmp_path / "test_db.sqlite3")
    apply_migrations(db_file)

    connection = get_connection(db_file)
    try:
        save_player_features(connection, _make_features(session_id="session-1"))
        save_player_features(connection, _make_features(session_id="session-2"))

        row = connection.execute(
            "SELECT session_id FROM player_features WHERE player_id = ? ORDER BY id DESC LIMIT 1",
            ("player_test",),
        ).fetchone()
        assert row["session_id"] == "session-2"
    finally:
        connection.close()
