"""Clusters callback handlers"""
from aiogram import types
from aiogram.dispatcher import FSMContext

from callbacks.base import handle_cancel
from callbacks.main_menu import handle_groups
from exceptions import NotExist
from handlers.bot_handlers import KeyboardConstructor
from handlers.database_handlers import ClusterHandler
from handlers.states import RenameClusterState, AddAddressState
from schema.bot_schema import CallbackDataModel


async def handle_view_cluster_addresses(callback: types.CallbackQuery):
    """Handle cluster addresses list"""
    data = CallbackDataModel.parse_raw(callback.data)
    handler = ClusterHandler()
    cluster = handler.get_cluster_by_id(data.id)
    msg = '<b>Addresses:</b>\n'
    msg += '\n'.join([f"{x.address.wallet} /address_{x.address.id}" for x in cluster.addresses])
    await callback.message.answer(msg)


async def handle_rename_cluster(callback: types.CallbackQuery, state: FSMContext):
    """Handle rename cluster"""
    data = CallbackDataModel.parse_raw(callback.data)
    await state.set_state(RenameClusterState.cluster_name)
    await state.update_data(cluster_id=data.id)
    msg = 'Input new cluster name'
    await callback.message.answer(msg, reply_markup=KeyboardConstructor.get_cancel_button())


async def handle_rename_cluster_set_name(message: types.Message, state: FSMContext):
    """Set new cluster name"""
    if message.text == 'Cancel':
        await handle_cancel(message, state)
    else:
        data = await state.get_data()
        handler = ClusterHandler()
        result = handler.rename_cluster(data['cluster_id'], message.text)
        if result is None:
            await state.reset_state(with_data=True)
            message.text = 'cluster_{}'.format(data['cluster_id'])
            msg = 'Success'
            await message.answer(msg, reply_markup=KeyboardConstructor.get_base_reply_keyboard())
            await handle_cluster_detail(message)
        else:
            msg = 'Error. Please try again. Note: length of name must be in [1, 28]'
            await message.answer(msg)


async def handle_cluster_detail(message: types.Message):
    """Handle cluster detail"""
    cluster_id = message.text.rsplit('_', 1)[1]
    handler = ClusterHandler()
    cluster = handler.get_cluster_by_id(int(cluster_id))
    msg, markup = KeyboardConstructor.get_cluster_detail(cluster)
    await message.answer(msg, reply_markup=markup)


async def add_group(message: types.Message, state: FSMContext):
    """Add new cluster"""
    if message.text == 'Cancel':
        await handle_cancel(message, state)

    else:
        handler = ClusterHandler()
        result = handler.add_cluster(message.from_user.id, message.text)
        if result is None:
            buttons = KeyboardConstructor.get_base_reply_keyboard()
            await state.reset_state(with_data=True)
            await message.answer('Success', reply_markup=buttons)
        else:
            msg = 'Error. Please try again. Note: length of name must be in [1, 28]'
            await message.answer(msg)


async def handle_mute_cluster(callback: types.CallbackQuery):
    """Toggle mute/unmute cluster"""
    data = CallbackDataModel.parse_raw(callback.data)
    handler = ClusterHandler()
    handler.toggle_mute(data.id)
    callback.message.text = 'cluster_{}'.format(data.id)
    await callback.answer('Success')
    await handle_cluster_detail(callback.message)


async def handle_delete_cluster(callback: types.CallbackQuery):
    """Delete cluster"""
    data = CallbackDataModel.parse_raw(callback.data)
    handler = ClusterHandler()
    try:
        handler.delete_cluster(data.id)
    except NotExist:
        await callback.message.answer('Cluster not exist')
    else:
        await callback.message.answer('Success')
    callback.message.from_user = callback.from_user
    await handle_groups(callback.message)


async def handle_add_address(callback: types.CallbackQuery, state: FSMContext):
    """Add address to cluster"""
    data = CallbackDataModel.parse_raw(callback.data)
    await state.set_state(AddAddressState.wallet)
    await state.update_data(cluster_id=data.id)
    msg = 'Input address'
    buttons = KeyboardConstructor.get_cancel_button()
    await callback.message.answer(msg, reply_markup=buttons)
