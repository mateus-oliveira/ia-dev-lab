"""Worker publisher: publica lotes de eventos sintéticos de jogadores no RabbitMQ.

Executado como processo de longa duração (ver `Makefile`, alvo
`publisher`). A cada ciclo, simula os dois jogadores de teste
configurados (`PLAYER_USERNAME_1`/`PLAYER_USERNAME_2`) com uma persona da
Taxonomia de Bartle sorteada independentemente para cada um, e publica um
lote de 15 a 20 eventos recentes de cada jogador em uma única fila
durável, usando o exchange default do RabbitMQ (ADR 0007). O ciclo se
repete no intervalo configurado em `PUBLISHER_INTERVAL_SECONDS`, até o
processo ser interrompido manualmente (`Ctrl+C`).
"""

import json
import os
import time
from typing import Any

import pika

from player_modeling.simulator.batch import build_player_batch


def get_connection_parameters() -> pika.ConnectionParameters:
    """Monta os parâmetros de conexão com o RabbitMQ a partir de variáveis de ambiente.

    Todas as variáveis (`RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USER`,
    `RABBITMQ_PASSWORD`) são obrigatórias — sem valores padrão hardcoded,
    devem estar definidas no `.env` (ver `.env.example`).

    :return: parâmetros de conexão prontos para `pika.BlockingConnection`.
    """
    host = os.environ["RABBITMQ_HOST"]
    port = int(os.environ["RABBITMQ_PORT"])
    user = os.environ["RABBITMQ_USER"]
    password = os.environ["RABBITMQ_PASSWORD"]
    credentials = pika.PlainCredentials(user, password)
    return pika.ConnectionParameters(host=host, port=port, credentials=credentials)


def get_queue_name() -> str:
    """Retorna o nome da fila configurado via variável de ambiente.

    `RABBITMQ_QUEUE` é obrigatória — sem valor padrão hardcoded, deve
    estar definida no `.env` (ver `.env.example`).

    :return: nome da fila RabbitMQ usada para publicar os lotes de eventos.
    """
    return os.environ["RABBITMQ_QUEUE"]


def publish_batch(
    batch: dict[str, Any],
    connection_parameters: pika.ConnectionParameters | None = None,
    queue_name: str | None = None,
) -> None:
    """Publica um lote de eventos na fila RabbitMQ.

    Declara a fila como durável e publica no exchange default (routing
    key igual ao nome da fila), com a mensagem marcada como persistente.

    :param connection_parameters: parâmetros de conexão customizados
        (usado nos testes para não depender de um broker real); usa as
        variáveis de ambiente se omitido.
    :param batch: mensagem a publicar, como retornada por
        `player_modeling.simulator.batch.build_player_batch`.
    :param queue_name: nome da fila customizado (útil para testes); usa a
        variável de ambiente `RABBITMQ_QUEUE` se omitido.
    """
    connection_parameters = connection_parameters or get_connection_parameters()
    queue_name = queue_name or get_queue_name()

    connection = pika.BlockingConnection(connection_parameters)
    try:
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=json.dumps(batch).encode("utf-8"),
            properties=pika.BasicProperties(delivery_mode=2, content_type="application/json"),
        )
    finally:
        connection.close()


def get_player_usernames() -> tuple[str, str]:
    """Retorna os dois jogadores de teste configurados via variável de ambiente.

    `PLAYER_USERNAME_1` e `PLAYER_USERNAME_2` são obrigatórias — sem
    valores padrão hardcoded, devem estar definidas no `.env` (ver
    `.env.example`). São os `player_id` para os quais o publisher publica
    eventos a cada ciclo, permitindo testar isolamento de dados entre
    contas conhecidas (ex.: registradas via `POST /auth/register`).

    :return: tupla `(PLAYER_USERNAME_1, PLAYER_USERNAME_2)`.
    """
    return os.environ["PLAYER_USERNAME_1"], os.environ["PLAYER_USERNAME_2"]


def get_publish_interval_seconds() -> float:
    """Retorna o intervalo, em segundos, entre ciclos de publicação.

    `PUBLISHER_INTERVAL_SECONDS` é obrigatória — sem valor padrão
    hardcoded, deve estar definida no `.env` (ver `.env.example`).

    :return: intervalo em segundos entre ciclos consecutivos.
    """
    return float(os.environ["PUBLISHER_INTERVAL_SECONDS"])


def publish_cycle() -> None:
    """Gera e publica um lote de eventos para cada jogador de teste configurado.

    Publica uma mensagem para `PLAYER_USERNAME_1` e outra para
    `PLAYER_USERNAME_2`, cada uma com uma persona sorteada
    independentemente (ver `player_modeling.simulator.batch.build_player_batch`).
    """
    for player_id in get_player_usernames():
        batch = build_player_batch(player_id=player_id)
        publish_batch(batch)
        print(
            f"Publicado lote de {len(batch['events'])} eventos do jogador "
            f"{batch['player_id']} (sessao {batch['session_id']}) na fila "
            f"'{get_queue_name()}'."
        )


def main() -> None:
    """Publica ciclos de eventos periodicamente até ser interrompido (Ctrl+C)."""
    interval_seconds = get_publish_interval_seconds()
    try:
        while True:
            publish_cycle()
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("Publisher interrompido.")


if __name__ == "__main__":
    main()
