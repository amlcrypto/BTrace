"""Addresses callback handlers"""
from aiogram import types
from aiogram.dispatcher import FSMContext

from callbacks.base import handle_cancel
from callbacks.clusters import handle_view_cluster_addresses
from exceptions import NotExist, InvalidName
from handlers.bot_handlers import KeyboardConstructor
from handlers.database_handlers import AddressesHandler
from handlers.kafka_handlers import send_data
from handlers.states import AddAddressState, RenameAddressState
from logger import LOGGER
from schema.bot_schema import CallbackDataModel


async def get_address(message: types.Message, state: FSMContext):
    """Get address wallet"""
    if message.text == 'Cancel':
        await handle_cancel(message, state)
    else:
        await state.update_data(wallet=message.text)
        await state.set_state(AddAddressState.blockchain)
        msg = 'Choose blockchain'
        try:
            chains = AddressesHandler().get_blockchains()
        except Exception as e:
            LOGGER.error(str(e))
        else:
            markup = KeyboardConstructor.get_blockchains_choices(chains)
            await message.answer(msg, reply_markup=markup)


async def get_blockchain(callback: types.CallbackQuery, state: FSMContext):
    """Get blockchain for address"""
    if isinstance(callback, types.Message) and callback.text == 'Cancel':
        await handle_cancel(callback, state)
    elif isinstance(callback, types.Message):
        pass
    else:
        data = CallbackDataModel.parse_raw(callback.data)
        await state.update_data(blockchain=data.id)
        await state.set_state(AddAddressState.name)
        msg = 'Input name'
        await callback.answer('')
        await callback.message.answer(msg)


async def get_name(message: types.Message, state: FSMContext):
    """Get name and add address to database"""
    if message.text == 'Cancel':
        await handle_cancel(message, state)
    elif len(message.text) > 100:
        await message.answer('Address too long (must be max 100 characters)')
    else:
        data = await state.get_data()
        cluster_id, wallet, blockchain = data.values()
        name = message.text
        handler = AddressesHandler()
        try:
            handler.add_address(cluster_id, wallet, blockchain, name)
            await send_data('add_address', wallet, blockchain, cluster_id=cluster_id)
        except (NotExist, InvalidName) as e:
            msg = str(e)
            await message.answer(msg)
        else:
            msg = 'Address sent to trace. Please wait for confirm message'
            buttons = KeyboardConstructor.get_base_reply_keyboard()
            await state.reset_state(with_data=True)
            await message.answer(msg, reply_markup=buttons)


async def handle_address_detail(message: types.Message):
    """Handle detail info about address"""
    address_id = int(message.text.rsplit('_', 1)[1])
    try:
        address = AddressesHandler().get_address_by_id(address_id)
    except NotExist as e:
        msg = str(e)
        markup = KeyboardConstructor.get_base_reply_keyboard()
        await message.answer(msg, reply_markup=markup)
    else:
        msg, markup = KeyboardConstructor.get_address_detail(address)
        await message.answer(msg, reply_markup=markup, disable_web_page_preview=True)


async def handle_rename_address(callback: types.CallbackQuery, state: FSMContext):
    """Start rename address dialog"""
    data = CallbackDataModel.parse_raw(callback.data)
    await state.set_state(RenameAddressState.address_name)
    await state.update_data(link_id=data.id)
    msg = 'Input new address name'
    await callback.answer('')
    await callback.message.answer(msg, reply_markup=KeyboardConstructor.get_cancel_button())


async def handle_rename_address_set_name(message: types.Message, state: FSMContext):
    """Set new name for address"""
    if message.text == 'Cancel':
        await handle_cancel(message, state)
    else:
        data = await state.get_data()
        try:
            AddressesHandler().rename_address(data['link_id'], message.text)
        except (NotExist, InvalidName) as e:
            await message.answer(str(e))
        else:
            markup = KeyboardConstructor.get_base_reply_keyboard()
            await state.reset_state(with_data=True)
            message.text = 'address_{}'.format(data['link_id'])
            msg = 'Success'
            await message.answer(msg, reply_markup=markup)
            await handle_address_detail(message)


async def handle_mute_address(callback: types.CallbackQuery):
    """Toggle mute/unmute address"""
    data = CallbackDataModel.parse_raw(callback.data)
    try:
        address = AddressesHandler().toggle_mute_address(data.id)
    except NotExist as e:
        msg = str(e)
        markup = KeyboardConstructor.get_base_reply_keyboard()
        await callback.answer('')
        await callback.message.answer(msg, reply_markup=markup)
    else:
        msg, markup = KeyboardConstructor.get_address_detail(address)
        callback.message.text = 'address_{}'.format(data.id)
        await callback.message.edit_text(msg)
        await callback.message.edit_reply_markup(markup)
        await callback.answer('Success')


async def handle_delete_address(callback: types.CallbackQuery):
    """Delete address from cluster"""
    data = CallbackDataModel.parse_raw(callback.data)
    cluster_id, deleted = AddressesHandler().delete_address(data.id)
    if deleted:
        address, blockchain = deleted
        await send_data(action='delete_address', wallet=address, blockchain_id=blockchain, cluster_id=cluster_id)
    data.action = 'view_addresses'
    data.id = cluster_id
    callback.data = data.json()
    await callback.answer('Success')
    await handle_view_cluster_addresses(callback)
