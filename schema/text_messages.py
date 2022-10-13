"""Module contains objects with text messages"""
import os
from pathlib import Path

from pydantic import BaseModel


class TextMessage(BaseModel):
    eng: str
    rus: str


class TextMessages:

    __messages = {}

    @classmethod
    def add_message(cls, name: str, obj: TextMessage):
        key = name.split('.')[0]
        cls.__messages[key] = obj

    @classmethod
    def get_message(cls, name: str) -> TextMessage:
        return cls.__messages.get(name)


for filename in os.listdir(f"{Path(__file__).resolve().parent.parent}/text/"):
    filename = str(filename)
    if filename.endswith('txt'):

        with open(f"{Path(__file__).resolve().parent.parent}/text/{filename}", 'r', encoding='utf-8') as f:
            rows = f.readlines()
            text = ''.join(rows)
            TextMessages.add_message(filename, TextMessage(
                eng=text,
                rus=text
            ))
