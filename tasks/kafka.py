import asyncio
import functools
import json
import os
import uuid
from datetime import datetime

from confluent_kafka import Producer

from schema_registry.registry import validate_event
from tasks import crud

import confluent_kafka

from tasks.dependencies import get_db
from tasks.models import Task, User

kafka_actions = {
    "accounts": crud.add_user,
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
            validate_event(message.topic, message.value)
            kafka_actions[message.topic](db, message.value)
    finally:
        consumer.close()


def send_cud_task(task: Task):
    data = {
        "event_id": str(uuid.uuid4()),
        "event_version": 1,
        "event_time": datetime.now().strftime("%y-%m-%d %H:%M:%s"),
        "producer": "task",
        "data": {
            "public_id": task.public_id,
            "title": task.title,
            "assigner_id": task.assigner_id,
            "status": task.status,
            "created_by": task.created_by,
        },
    }
    validate_event('tasks', data)
    producer.produce('tasks', json.dumps(data))


def send_assigned_task(task: Task, assigner: User):
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
    validate_event('tasks.assigned', data)
    producer.produce('tasks.assigned', json.dumps(data))


def send_done_task(task: Task, assigner: User):
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
    validate_event('tasks.done', data)
    producer.produce('tasks.done', json.dumps(data))
