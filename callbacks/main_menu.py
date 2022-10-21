"""Main menu handlers"""
import os

from aiogram import types
from aiogram.dispatcher import FSMContext

from handlers.bot_handlers import KeyboardConstructor
from handlers.database_handlers import UsersHandler
from handlers.states import AddClusterState
from logger import LOGGER
from schema.text_messages import TextMessages
from schema.bot_schema import CallbackDataModel


async def handle_alert_history_csv(callback: types.CallbackQuery):
    """Returns csv alert history for user"""
    data = CallbackDataModel.parse_raw(callback.data)
    filename = KeyboardConstructor.create_alert_history_report(data.id)
    try:
        with open(filename, 'rb') as f:
            await callback.answer('Success', show_alert=False)
            await callback.bot.send_document(chat_id=callback.from_user.id, document=f)
    except Exception as e:
        LOGGER.error(str(e))
        await callback.answer('Error')
        await callback.message.answer('Error. Try again later or connect to administration')
    finally:
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass


async def handle_help(message: types.Message):
    """Handle help"""
    msg = TextMessages.get_message('help')
    await message.answer(msg.text)


async def handle_profile(message: types.Message):
    """Handle users profile"""
    handler = UsersHandler()
    user = handler.get_user_by_id(message.from_user.id)
    button = types.InlineKeyboardButton(
        text='Get my alert history',
        callback_data=CallbackDataModel(
            action='alert_history',
            id=user.id
        ).json()
    )
    markup = types.InlineKeyboardMarkup(inline_keyboard=[[button]])
    if not user:
        msg = 'You are not registered yet. type "/start" to register'
        await message.answer(msg)
    else:
        await message.answer(str(user), reply_markup=markup)


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
    if not user:
        msg = 'You are not registered yet. type "/start" to register'
        await message.answer(msg)
    else:
        msg = KeyboardConstructor.get_clusters_list(user)
        await message.answer(msg or "You don't added any clusters yet")
