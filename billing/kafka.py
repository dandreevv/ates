import asyncio
import functools
import json
import os
import uuid
from datetime import datetime

from confluent_kafka import Producer

from billing.models import Task
from schema_registry.registry import validate_event
from billing import crud

import confluent_kafka

from billing.dependencies import get_db

kafka_actions = {
    "tasks": crud.add_task,
    "tasks.assigned": crud.add_fee_transaction,
    "tasks.done": crud.add_cost_transaction,
    "billing": crud.done_billing,
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
            if message.topic != "billing":
                validate_event(message.topic, message.value)
            kafka_actions[message.topic](db, message.value)
    finally:
        consumer.close()


def send_costed_task(task: Task):
    data = {
        "event_id": str(uuid.uuid4()),
        "event_version": 1,
        "event_time": datetime.now().strftime("%y-%m-%d %H:%M:%s"),
        "producer": "task",
        "data": {
            "assigner_pub_id": assigner.public_id,
            "task_pub_id": task.public_id,
        },
    }
    validate_event('billing.costed', data)
    producer.produce('billing.costed', json.dumps(data))
