import asyncio
import functools
import os

from confluent_kafka import Producer

from tasks import crud

import confluent_kafka

from tasks.dependencies import get_db

kafka_actions = {
    "accounts": crud.add_user,
    "accounts.updated": crud.update_user,
}

producer = Producer(
    {
        "bootstrap.servers": os.environ["KAFKA_BOOTSTRAP_SERVERS"],
    }
)


async def consume(topics):
    config = {
        "bootstrap.servers": os.environ["KAFKA_BOOTSTRAP_SERVERS"],
        "group.id": "consumer-group-name",
    }
    consumer = confluent_kafka.Consumer(config)
    consumer.subscribe(topics)
    loop = asyncio.get_running_loop()
    poll = functools.partial(consumer.poll, 0.1)
    try:
        while True:
            message = await loop.run_in_executor(None, poll)
            if message is None:
                continue
            if message.error():
                continue
            db = get_db()
            kafka_actions[message.topic](db, message.value)
    finally:
        consumer.close()
