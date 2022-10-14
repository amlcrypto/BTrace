"""Base callback functions"""
from aiogram import types
from aiogram.dispatcher import FSMContext

from handlers.bot_handlers import KeyboardConstructor
from handlers.database_handlers import UsersHandler
from schema.text_messages import TextMessages


async def handle_cancel(message: types.Message, state: FSMContext):
    """Handle cancel command"""
    await state.reset_state(with_data=True)
    msg = 'Cancelled'
    buttons = KeyboardConstructor.get_base_reply_keyboard()
    await message.answer(msg, reply_markup=buttons)


async def handle_start(message: types.Message):
    """Handle 'start' command"""
    handler = UsersHandler()
    user_id = message.from_user.id
    user = handler.get_user_by_id(user_id)
    if not user:
        handler.add_user(user_id)

    msg = TextMessages.get_message('start')
    buttons = KeyboardConstructor.get_base_reply_keyboard()

    await message.answer(msg.text.format(message.from_user.full_name), reply_markup=buttons)
