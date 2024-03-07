import os

from confluent_kafka import Producer

producer = Producer(
    {'bootstrap.servers': os.environ["KAFKA_BOOTSTRAP_SERVERS"]}
)
