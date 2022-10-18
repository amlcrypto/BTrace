"""Kafka handlers module"""

from aiogram import Bot
from aiokafka import AIOKafkaConsumer, TopicPartition
from kafka import KafkaProducer

from config import settings
from handlers.bot_handlers import NotificationHandler
from handlers.database_handlers import AddressesHandler
from schema.kafka_schema import Outgoing, Incoming


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


async def consume_data(bot: Bot):
    """Consume data from kafka"""
    handler = AddressesHandler()
    topics = [x.tag for x in handler.get_blockchains()]
    consumer = AIOKafkaConsumer(
        *topics,
        bootstrap_servers=[settings.kafka],
        auto_offset_reset='latest',
        enable_auto_commit=False,
        group_id='BOT',
        value_deserializer=lambda x: str(x.decode('utf-8')),
    )
    await consumer.start()
    try:
        async for message in consumer:
            result = await NotificationHandler.handle_notification(Incoming.parse_raw(message.value), bot)
            if result:
                send_data('delete_address', result.wallet, result.blockchain)
            tp = TopicPartition(message.topic, message.partition)
            await consumer.commit({tp: message.offset + 1})
    finally:
        await consumer.stop()

