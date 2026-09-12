"""Testes do consumidor RabbitMQ (callback de mensagem, sem broker real)."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from player_modeling.api.database import get_connection
from player_modeling.worker.subscriber import (
    get_connection_parameters,
    get_queue_name,
    make_on_message_callback,
)


class _FakeMethod:
    """Substituto de `pika.spec.Basic.Deliver` para os testes (só expõe delivery_tag)."""

    def __init__(self, delivery_tag: int) -> None:
        self.delivery_tag = delivery_tag


class _FakeChannel:
    """Substituto de `BlockingChannel` para inspecionar ack/nack nos testes."""

    def __init__(self) -> None:
        self.acked: list[int] = []
        self.nacked: list[tuple[int, bool]] = []

    def basic_ack(self, delivery_tag: int) -> None:
        self.acked.append(delivery_tag)

    def basic_nack(self, delivery_tag: int, requeue: bool = True) -> None:
        self.nacked.append((delivery_tag, requeue))


def _valid_event() -> dict[str, Any]:
    return {
        "event_id": "evt-1",
        "session_id": "session-1",
        "player_id": "player_test",
        "timestamp": "2026-01-01T00:00:00",
        "event_type": "attack",
        "decision_time_ms": 500,
        "outcome": "success",
    }


def test_on_message_persists_and_acks_valid_message(
    tmp_path: Path, apply_migrations: Callable[[str], None]
) -> None:
    """Mensagem válida é agregada, persistida e confirmada (ack).

    :param tmp_path: Diretório temporário fornecido pelo pytest.
    :param apply_migrations: Fixture que aplica `alembic upgrade head` a um banco de teste.
    """
    db_file = str(tmp_path / "test_db.sqlite3")
    apply_migrations(db_file)
    connection = get_connection(db_file)

    fake_channel = _FakeChannel()
    on_message = make_on_message_callback(connection)

    body = json.dumps(
        {"player_id": "player_test", "session_id": "session-1", "events": [_valid_event()]}
    ).encode("utf-8")

    on_message(
        cast(BlockingChannel, fake_channel),
        cast(Basic.Deliver, _FakeMethod(delivery_tag=1)),
        cast(BasicProperties, None),
        body,
    )

    assert fake_channel.acked == [1]
    assert fake_channel.nacked == []

    row = connection.execute(
        "SELECT * FROM player_features WHERE player_id = ?", ("player_test",)
    ).fetchone()
    assert row is not None
    assert row["session_id"] == "session-1"
    connection.close()


def test_on_message_nacks_malformed_message_without_requeue(
    tmp_path: Path, apply_migrations: Callable[[str], None]
) -> None:
    """Mensagem malformada é descartada (nack sem requeue), sem interromper o consumo.

    :param tmp_path: Diretório temporário fornecido pelo pytest.
    :param apply_migrations: Fixture que aplica `alembic upgrade head` a um banco de teste.
    """
    db_file = str(tmp_path / "test_db.sqlite3")
    apply_migrations(db_file)
    connection = get_connection(db_file)

    fake_channel = _FakeChannel()
    on_message = make_on_message_callback(connection)

    on_message(
        cast(BlockingChannel, fake_channel),
        cast(Basic.Deliver, _FakeMethod(delivery_tag=7)),
        cast(BasicProperties, None),
        b"not-json",
    )

    assert fake_channel.nacked == [(7, False)]
    assert fake_channel.acked == []

    row = connection.execute("SELECT * FROM player_features").fetchone()
    assert row is None
    connection.close()


def test_get_connection_parameters_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Os parâmetros de conexão são lidos das variáveis de ambiente configuradas."""
    monkeypatch.setenv("RABBITMQ_HOST", "broker.local")
    monkeypatch.setenv("RABBITMQ_PORT", "5673")
    monkeypatch.setenv("RABBITMQ_USER", "test-user")
    monkeypatch.setenv("RABBITMQ_PASSWORD", "test-pass")

    params = get_connection_parameters()

    assert params.host == "broker.local"
    assert params.port == 5673
    assert params.credentials.username == "test-user"  # type: ignore[union-attr]
    assert params.credentials.password == "test-pass"  # type: ignore[union-attr]


def test_get_connection_parameters_requires_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Os parâmetros de conexão são obrigatórios: sem valores padrão hardcoded."""
    monkeypatch.delenv("RABBITMQ_HOST", raising=False)
    with pytest.raises(KeyError):
        get_connection_parameters()


def test_get_queue_name_requires_environment_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    """RABBITMQ_QUEUE é obrigatória: sem valor padrão hardcoded."""
    monkeypatch.delenv("RABBITMQ_QUEUE", raising=False)
    with pytest.raises(KeyError):
        get_queue_name()
