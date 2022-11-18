"""Kafka handlers module"""

from aiogram import Bot
from aiokafka import AIOKafkaConsumer, TopicPartition, AIOKafkaProducer

from config import settings
from handlers.bot_handlers import NotificationHandler
from handlers.database_handlers import AddressesHandler
from logger import LOGGER
from schema.kafka_schema import Outgoing, Incoming


async def send_data(action: str, wallet: str, blockchain_id: int, cluster_id: int = 0):
    """Send data to handler"""
    try:
        blockchain = AddressesHandler().get_blockchain_by_id(blockchain_id)
    except Exception as e:
        LOGGER.error(str(e))
    topic = f"{blockchain.tag}_TO_CHECKER"
    msg = Outgoing(
        action=action,
        wallet=wallet,
        blockchain=blockchain_id,
        cluster_id=cluster_id
    )
    producer = AIOKafkaProducer(
        bootstrap_servers=[settings.kafka]
    )
    await producer.start()
    try:
        await producer.send(topic, msg.json().encode('utf-8'))
    finally:
        await producer.stop()


async def consume_data(bot: Bot):
    """Consume data from kafka"""
    try:
        handler = AddressesHandler()
    except Exception as e:
        LOGGER.error(str(e))
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
                await send_data('delete_address', result.wallet, result.blockchain)
            tp = TopicPartition(message.topic, message.partition)
            await consumer.commit({tp: message.offset + 1})
    finally:
        await consumer.stop()
    del handler
