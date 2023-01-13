"""Kafka data models"""
from typing import List, Optional

from pydantic import BaseModel


class Outgoing(BaseModel):
    """Outgoing message"""
    action: str
    wallet: str
    blockchain: int
    cluster_id: int


class Transaction(BaseModel):
    """Single transaction for alert"""
    tx_hash: Optional[str]
    src: str
    dst: str
    value: float
    token: str
    created_at: float


class Incoming(BaseModel):
    """Incoming message"""
    action: str
    state: Optional[int]
    cluster_id: Optional[int]
    blockchain: int
    wallet: str
    transactions: List[Transaction]
    auto_add: List[str]
