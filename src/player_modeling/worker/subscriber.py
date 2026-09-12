"""Worker subscriber: consome eventos do RabbitMQ e persiste features agregadas.

Executado como processo de longa duração (ver `Makefile`, alvo
`subscriber`). Consome continuamente a fila `RABBITMQ_QUEUE`, agrega cada
lote de eventos recebido em uma linha de features
(`player_modeling.worker.features.extract_features`) e a persiste em
`player_features` (ADR 0008). Mensagens malformadas são descartadas sem
reprocessamento, para não interromper o consumo.
"""

import logging
import os
import sqlite3
from collections.abc import Callable

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from player_modeling.api.database import get_connection
from player_modeling.worker.features import extract_features
from player_modeling.worker.messages import InvalidMessageError, parse_message
from player_modeling.worker.repository import save_player_features

logger = logging.getLogger(__name__)

OnMessageCallback = Callable[[BlockingChannel, Basic.Deliver, BasicProperties, bytes], None]


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

    :return: nome da fila RabbitMQ consumida pelo worker.
    """
    return os.environ["RABBITMQ_QUEUE"]


def make_on_message_callback(db_connection: sqlite3.Connection) -> OnMessageCallback:
    """Monta o callback de mensagem do consumidor, ligado a uma conexão SQLite.

    :param db_connection: conexão SQLite já aberta, reaproveitada a cada mensagem.

    :return: callback compatível com `channel.basic_consume`.
    """

    def on_message(
        channel: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ) -> None:
        try:
            message = parse_message(body)
        except InvalidMessageError as exc:
            logger.warning("Mensagem invalida descartada: %s", exc)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        features = extract_features(message["session_id"], message["player_id"], message["events"])
        save_player_features(db_connection, features)
        channel.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(
            "Persistidas features do jogador %s (sessao %s, %s eventos)",
            features["player_id"],
            features["session_id"],
            features["n_events"],
        )

    return on_message


def main() -> None:
    """Consome a fila continuamente, persistindo features, até ser interrompido (Ctrl+C)."""
    logging.basicConfig(level=logging.INFO)

    connection = pika.BlockingConnection(get_connection_parameters())
    channel = connection.channel()
    queue_name = get_queue_name()
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_qos(prefetch_count=1)

    db_connection = get_connection()
    try:
        channel.basic_consume(
            queue=queue_name, on_message_callback=make_on_message_callback(db_connection)
        )
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()
            print("Subscriber interrompido.")
    finally:
        db_connection.close()
        connection.close()


if __name__ == "__main__":
    main()
