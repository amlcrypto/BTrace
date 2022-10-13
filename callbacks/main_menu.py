"""Main menu handlers"""
from aiogram import types
from aiogram.dispatcher import FSMContext

from handlers.bot_handlers import KeyboardConstructor
from handlers.database_handlers import UsersHandler
from handlers.states import AddClusterState
from schema.text_messages import TextMessages


async def handle_help(message: types.Message):
    msg = TextMessages.get_message('help')
    await message.answer(msg.rus)


async def handle_profile(message: types.Message):
    handler = UsersHandler()
    user = handler.get_user_by_id(message.from_user.id)
    await message.answer(str(user))


async def handle_group_add(message: types.Message, state: FSMContext):
    """Start add cluster dialog"""
    await state.set_state(AddClusterState.cluster_name)
    msg = 'Input cluster name'
    buttons = KeyboardConstructor.get_cancel_button()

    await message.answer(msg, reply_markup=buttons)


async def handle_groups(message: types.Message):
    """Handle 'My clusters' command"""
    handler = UsersHandler()
    user = handler.get_user_by_id(message.from_user.id)
    msg = KeyboardConstructor.get_clusters_list(user)
    await message.answer(msg or "You don't added any clusters yet")