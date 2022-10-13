"""Bot handler filters"""
from typing import Union

from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.filters.state import State, StatesGroup

from handlers.states import AddAddressState, AddClusterState
from schema.bot_schema import CallbackDataModel


class CallbackDataActionFilter(BoundFilter):
    key = 'query_action'

    def __init__(self, action: str):
        self.action = action

    async def check(self, callback: types.CallbackQuery) -> bool:
        if not callback.data:
            return False

        data = CallbackDataModel.parse_raw(callback.data)
        return data.action == self.action
