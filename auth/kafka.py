import json
import os
import uuid
from datetime import datetime

from confluent_kafka import Producer

from schema_registry.registry import validate_event

producer = Producer(
    {'bootstrap.servers': os.environ["KAFKA_BOOTSTRAP_SERVERS"]}
)


def send_user(data: dict):
    data = {
        "event_id": str(uuid.uuid4()),
        "event_version": 1,
        "event_time": datetime.now().strftime("%y-%m-%d %H:%M:%s"),
        "producer": "auth",
        "data": {
            **data,
        },
    }
    validate_event('accounts', data)
    producer.produce('accounts.updated', json.dumps(data))
