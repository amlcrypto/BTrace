"""Kafka data models"""
from typing import List

from pydantic import BaseModel


class Outgoing(BaseModel):
    """Outgoing message"""
    action: str
    wallet: str
    blockchain: int


class Transaction(BaseModel):
    """Single transaction for alert"""
    src: str
    dst: str
    value: float
    token: str = 'EVER'
    created_at: float


class Incoming(BaseModel):
    """Incoming message"""
    blockchain: int
    wallet: str
    transactions: List[Transaction]
