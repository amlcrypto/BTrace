"""Kafka handlers module"""

from kafka import KafkaProducer

from config import settings
from handlers.database_handlers import AddressesHandler
from schema.kafka_schema import Outgoing


def send_data(action: str, wallet: str, blockchain_id: int):
    """Send data to handler"""
    blockchain = AddressesHandler().get_blockchain_by_id(blockchain_id)
    topic = f"{blockchain.tag}_TO_CHECKER"
    msg = Outgoing(
        action=action,
        wallet=wallet,
        blockchain=blockchain_id
    )
    producer = KafkaProducer(
        bootstrap_servers=[settings.kafka]
    )
    producer.send(topic, key=topic.encode('utf-8'), value=msg.json().encode('utf-8'))
