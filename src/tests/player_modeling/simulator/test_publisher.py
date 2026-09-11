"""Testes unitários da montagem do lote e do publisher (pika mockado)."""

import json
from typing import Any

import pika
import pytest

from player_modeling.simulator import publisher
from player_modeling.simulator.batch import MAX_BATCH_EVENTS, MIN_BATCH_EVENTS, build_player_batch


def test_build_player_batch_never_includes_persona() -> None:
    """A mensagem publicada nunca inclui a persona/true_persona do jogador simulado."""
    batch = build_player_batch()

    assert set(batch.keys()) == {"player_id", "session_id", "events"}
    assert MIN_BATCH_EVENTS <= len(batch["events"]) <= MAX_BATCH_EVENTS

    serialized = json.dumps(batch).lower()
    assert "persona" not in serialized


def test_build_player_batch_events_share_player_and_session_id() -> None:
    """Todos os eventos do lote pertencem ao mesmo jogador/sessão simulados."""
    batch = build_player_batch(player_id="player_fixed", persona="Achiever")

    assert batch["player_id"] == "player_fixed"
    for event in batch["events"]:
        assert event["player_id"] == "player_fixed"
        assert event["session_id"] == batch["session_id"]


class _FakeChannel:
    """Substituto de `pika.channel.Channel` para inspecionar chamadas nos testes."""

    def __init__(self) -> None:
        self.declared_queues: list[tuple[str, bool]] = []
        self.published: list[dict[str, Any]] = []

    def queue_declare(self, queue: str, durable: bool = False) -> None:
        self.declared_queues.append((queue, durable))

    def basic_publish(
        self,
        exchange: str,
        routing_key: str,
        body: bytes,
        properties: pika.BasicProperties,
    ) -> None:
        self.published.append(
            {
                "exchange": exchange,
                "routing_key": routing_key,
                "body": body,
                "properties": properties,
            }
        )


class _FakeConnection:
    """Substituto de `pika.BlockingConnection` para não depender de um broker real."""

    def __init__(self, parameters: pika.ConnectionParameters) -> None:
        self.parameters = parameters
        self.channel_instance = _FakeChannel()
        self.closed = False

    def channel(self) -> _FakeChannel:
        return self.channel_instance

    def close(self) -> None:
        self.closed = True


def test_publish_batch_declares_durable_queue_and_publishes_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """publish_batch declara a fila como durável e publica no exchange default."""
    created_connections: list[_FakeConnection] = []

    def fake_blocking_connection(parameters: pika.ConnectionParameters) -> _FakeConnection:
        connection = _FakeConnection(parameters)
        created_connections.append(connection)
        return connection

    monkeypatch.setattr(pika, "BlockingConnection", fake_blocking_connection)

    batch = {"player_id": "player_test", "session_id": "session-1", "events": []}
    connection_parameters = pika.ConnectionParameters(host="fake-host")

    publisher.publish_batch(
        batch, connection_parameters=connection_parameters, queue_name="test_queue"
    )

    assert len(created_connections) == 1
    connection = created_connections[0]
    assert connection.closed is True

    channel = connection.channel_instance
    assert channel.declared_queues == [("test_queue", True)]
    assert len(channel.published) == 1

    published = channel.published[0]
    assert published["exchange"] == ""
    assert published["routing_key"] == "test_queue"
    assert json.loads(published["body"]) == batch
    assert published["properties"].delivery_mode == 2


def test_get_connection_parameters_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Os parâmetros de conexão são lidos das variáveis de ambiente configuradas."""
    monkeypatch.setenv("RABBITMQ_HOST", "broker.local")
    monkeypatch.setenv("RABBITMQ_PORT", "5673")
    monkeypatch.setenv("RABBITMQ_USER", "test-user")
    monkeypatch.setenv("RABBITMQ_PASSWORD", "test-pass")

    params = publisher.get_connection_parameters()

    assert params.host == "broker.local"
    assert params.port == 5673
    assert params.credentials.username == "test-user"  # type: ignore[union-attr]
    assert params.credentials.password == "test-pass"  # type: ignore[union-attr]


def test_get_queue_name_requires_environment_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    """RABBITMQ_QUEUE é obrigatória: sem valor padrão hardcoded."""
    monkeypatch.delenv("RABBITMQ_QUEUE", raising=False)
    with pytest.raises(KeyError):
        publisher.get_queue_name()


def test_get_connection_parameters_requires_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Os parâmetros de conexão são obrigatórios: sem valores padrão hardcoded."""
    monkeypatch.delenv("RABBITMQ_HOST", raising=False)
    with pytest.raises(KeyError):
        publisher.get_connection_parameters()


def test_get_player_usernames_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_player_usernames lê PLAYER_USERNAME_1/2 do ambiente."""
    monkeypatch.setenv("PLAYER_USERNAME_1", "player_alpha")
    monkeypatch.setenv("PLAYER_USERNAME_2", "player_beta")
    assert publisher.get_player_usernames() == ("player_alpha", "player_beta")


def test_get_player_usernames_requires_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PLAYER_USERNAME_1/2 são obrigatórias: sem valores padrão hardcoded."""
    monkeypatch.delenv("PLAYER_USERNAME_1", raising=False)
    with pytest.raises(KeyError):
        publisher.get_player_usernames()


def test_get_publish_interval_seconds_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_publish_interval_seconds lê PUBLISHER_INTERVAL_SECONDS do ambiente."""
    monkeypatch.setenv("PUBLISHER_INTERVAL_SECONDS", "5")
    assert publisher.get_publish_interval_seconds() == 5.0


def test_get_publish_interval_seconds_requires_environment_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PUBLISHER_INTERVAL_SECONDS é obrigatória: sem valor padrão hardcoded."""
    monkeypatch.delenv("PUBLISHER_INTERVAL_SECONDS", raising=False)
    with pytest.raises(KeyError):
        publisher.get_publish_interval_seconds()


def test_publish_cycle_publishes_one_batch_per_configured_player(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """publish_cycle publica um lote para PLAYER_USERNAME_1 e outro para PLAYER_USERNAME_2."""
    created_connections: list[_FakeConnection] = []

    def fake_blocking_connection(parameters: pika.ConnectionParameters) -> _FakeConnection:
        connection = _FakeConnection(parameters)
        created_connections.append(connection)
        return connection

    monkeypatch.setattr(pika, "BlockingConnection", fake_blocking_connection)
    monkeypatch.setenv("RABBITMQ_HOST", "broker.local")
    monkeypatch.setenv("RABBITMQ_PORT", "5672")
    monkeypatch.setenv("RABBITMQ_USER", "test-user")
    monkeypatch.setenv("RABBITMQ_PASSWORD", "test-pass")
    monkeypatch.setenv("RABBITMQ_QUEUE", "test_queue")
    monkeypatch.setenv("PLAYER_USERNAME_1", "player_alpha")
    monkeypatch.setenv("PLAYER_USERNAME_2", "player_beta")

    publisher.publish_cycle()

    assert len(created_connections) == 2
    published_player_ids = set()
    for connection in created_connections:
        assert len(connection.channel_instance.published) == 1
        body = json.loads(connection.channel_instance.published[0]["body"])
        published_player_ids.add(body["player_id"])

    assert published_player_ids == {"player_alpha", "player_beta"}


def test_main_loops_until_interrupted(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() publica ciclos repetidamente e encerra de forma limpa no Ctrl+C."""
    monkeypatch.setenv("PUBLISHER_INTERVAL_SECONDS", "60")
    cycle_calls: list[int] = []

    def fake_publish_cycle() -> None:
        cycle_calls.append(1)

    def fake_sleep(seconds: float) -> None:
        assert seconds == 60.0
        raise KeyboardInterrupt

    monkeypatch.setattr(publisher, "publish_cycle", fake_publish_cycle)
    monkeypatch.setattr(publisher.time, "sleep", fake_sleep)

    publisher.main()

    assert len(cycle_calls) == 1
