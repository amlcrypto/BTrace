"""Addresses callback handlers"""
from aiogram import types
from aiogram.dispatcher import FSMContext

from callbacks.base import handle_cancel
from callbacks.clusters import handle_cluster_detail
from exceptions import NotExist
from handlers.bot_handlers import KeyboardConstructor
from handlers.database_handlers import AddressesHandler
from handlers.states import AddAddressState
from schema.bot_schema import CallbackDataModel


async def get_address(message: types.Message, state: FSMContext):
    """Get address wallet"""
    if message.text == 'Cancel':
        await handle_cancel(message, state)
    else:
        await state.update_data(wallet=message.text)
        await state.set_state(AddAddressState.blockchain)
        msg = 'Choose blockchain'
        chains = AddressesHandler().get_blockchains()
        markup = KeyboardConstructor.get_blockchains_choices(chains)
        await message.answer(msg, reply_markup=markup)


async def get_blockchain(callback: types.CallbackQuery, state: FSMContext):
    """Get blockchain for address"""
    if isinstance(callback, types.Message) and callback.text == 'Cancel':
        await handle_cancel(callback, state)
    else:
        data = CallbackDataModel.parse_raw(callback.data)
        await state.update_data(blockchain=data.id)
        await state.set_state(AddAddressState.name)
        msg = 'Input name'
        await callback.message.answer(msg)


async def get_name(message: types.Message, state: FSMContext):
    """Get name and add address to database"""
    if message.text == 'Cancel':
        await handle_cancel(message, state)
    else:
        data = await state.get_data()
        cluster_id, wallet, blockchain = data.values()
        name = message.text
        handler = AddressesHandler()
        try:
            handler.add_address(cluster_id, wallet, blockchain, name)
        except NotExist as e:
            msg = str(e)
        else:
            msg = 'Success'

        buttons = KeyboardConstructor.get_base_reply_keyboard()
        await state.reset_state(with_data=True)
        await message.answer(msg, reply_markup=buttons)
        message.text = 'cluster_{}'.format(cluster_id)
        await handle_cluster_detail(message)

