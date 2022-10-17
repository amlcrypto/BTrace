"""Kafka data models"""


from pydantic import BaseModel


class Outgoing(BaseModel):
    """Outgoing message"""
    action: str
    wallet: str
    blockchain: int
