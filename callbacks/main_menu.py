"""Main menu handlers"""
import os

from aiogram import types
from aiogram.dispatcher import FSMContext

from handlers.bot_handlers import KeyboardConstructor
from handlers.database_handlers import UsersHandler
from handlers.states import AddClusterState, AddAddressState
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
    try:
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
    except Exception as e:
        LOGGER.error(str(e))
    finally:
        handler.session.dispose()


async def handle_group_add(message: types.Message, state: FSMContext):
    """Start add cluster dialog"""
    await state.set_state(AddClusterState.cluster_name)
    msg = 'Input cluster name'
    buttons = KeyboardConstructor.get_cancel_button()

    await message.answer(msg, reply_markup=buttons)


async def handle_groups(message: types.Message):
    """Handle 'My clusters' command"""
    handler = UsersHandler()
    try:
        user = handler.get_user_by_id(message.from_user.id)
        if not user:
            msg = 'You are not registered yet. type "/start" to register'
            await message.answer(msg)
        else:
            msg = KeyboardConstructor.get_clusters_list(user)
            await message.answer(msg or "You don't added any clusters yet")
    except Exception as e:
        LOGGER.error(str(e))
    finally:
        handler.session.dispose()


async def handle_choose_cluster(callback: types.CallbackQuery, state: FSMContext):
    data = CallbackDataModel.parse_raw(callback.data)
    await state.update_data(cluster_id=data.id)
    await state.set_state(AddAddressState.wallet)
    msg = 'Input address'
    buttons = KeyboardConstructor.get_cancel_button()
    await callback.answer('')
    await callback.message.answer(msg, reply_markup=buttons)


async def handle_add_address_main(message: types.Message, state: FSMContext):
    """Handler for add address main menu command"""
    handler = UsersHandler()
    try:
        user = handler.get_user_by_id(message.from_user.id)
        if not len(user.clusters):
            await state.update_data(cluster_id=None)
            await state.set_state(AddAddressState.wallet)
            msg = 'Input address'
            buttons = KeyboardConstructor.get_cancel_button()
        else:
            ids = [(i.name, i.id) for i in user.clusters]
            buttons = KeyboardConstructor.get_clusters_choices(ids)
            msg = 'Choose cluster'
        await message.answer(msg, reply_markup=buttons)
    finally:
        handler.session.dispose()
