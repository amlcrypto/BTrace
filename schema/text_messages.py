"""Module contains objects with text messages"""
import os
from pathlib import Path

from pydantic import BaseModel


class TextMessage(BaseModel):
    """Schema of abstract text message"""
    text: str


class TextMessages:
    """Text messages factory"""
    __messages = {}

    @classmethod
    def add_message(cls, name: str, obj: TextMessage):
        """Add message to factory"""
        key = name.split('.')[0]
        cls.__messages[key] = obj

    @classmethod
    def get_message(cls, name: str) -> TextMessage:
        """Returns message by name"""
        return cls.__messages.get(name)


for filename in os.listdir(f"{Path(__file__).resolve().parent.parent}/text/"):
    filename = str(filename)
    if filename.endswith('txt'):

        with open(f"{Path(__file__).resolve().parent.parent}/text/{filename}", 'r', encoding='utf-8') as f:
            rows = f.readlines()
            text = ''.join(rows)
            TextMessages.add_message(filename, TextMessage(
                text=text,
            ))
