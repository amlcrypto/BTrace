"""Bot handler filters"""

from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from schema.bot_schema import CallbackDataModel


class CallbackDataActionFilter(BoundFilter):
    """Filter by callback action param"""
    key = 'query_action'

    def __init__(self, action: str):
        self.action = action

    async def check(self, callback: types.CallbackQuery) -> bool:
        """Get callback and check for action"""
        if not callback.data:
            return False

        data = CallbackDataModel.parse_raw(callback.data)
        return data.action == self.action
