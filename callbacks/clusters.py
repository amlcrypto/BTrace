"""Clusters callback handlers"""
from aiogram import types
from aiogram.dispatcher import FSMContext

from callbacks.base import handle_cancel
from callbacks.main_menu import handle_groups
from exceptions import NotExist, InvalidName
from handlers.bot_handlers import KeyboardConstructor
from handlers.database_handlers import ClusterHandler
from handlers.states import RenameClusterState, AddAddressState
from logger import LOGGER
from schema.bot_schema import CallbackDataModel
from utils import parse_message


async def handle_view_cluster_addresses(callback: types.CallbackQuery):
    """Handle cluster addresses list"""
    data = CallbackDataModel.parse_raw(callback.data)
    page = data.data.get('page')
    handler = ClusterHandler()
    try:
        cluster = handler.get_cluster_by_id(data.id)
        if not cluster:
            await callback.answer('Cluster not exist')
            callback.message.from_user = callback.from_user
            await handle_groups(callback.message)
        else:
            msg, markup = KeyboardConstructor.get_addresses_list(cluster, page)
            await callback.answer('')
            await callback.message.answer(msg, reply_markup=markup)
    except Exception as e:
        LOGGER.error(str(e))
    finally:
        handler.session.dispose()


async def handle_rename_cluster(callback: types.CallbackQuery, state: FSMContext):
    """Handle rename cluster"""
    data = CallbackDataModel.parse_raw(callback.data)
    await state.set_state(RenameClusterState.cluster_name)
    await state.update_data(cluster_id=data.id)
    msg = 'Input new cluster name'
    await callback.answer('')
    await callback.message.answer(msg, reply_markup=KeyboardConstructor.get_cancel_button())


async def handle_rename_cluster_set_name(message: types.Message, state: FSMContext):
    """Set new cluster name"""
    if message.text == 'Cancel':
        await handle_cancel(message, state)
    else:
        data = await state.get_data()
        handler = ClusterHandler()
        try:
            handler.rename_cluster(data['cluster_id'], message.text)
        except (NotExist, InvalidName) as e:
            await message.answer(str(e))
        else:
            markup = KeyboardConstructor.get_base_reply_keyboard()
            await state.reset_state(with_data=True)
            message.text = 'cluster_{}'.format(data['cluster_id'])
            msg = 'Success'
            await message.answer(msg, reply_markup=markup)
            await handle_cluster_detail(message)
        finally:
            handler.session.dispose()


async def handle_cluster_detail(message: types.Message):
    """Handle cluster detail"""
    cluster_id = message.text.rsplit('_', 1)[1]
    handler = ClusterHandler()
    try:
        cluster = handler.get_cluster_by_id(int(cluster_id))
        if not cluster or cluster.user_id != int(message.from_user.id):
            await message.answer('Cluster not exist')
            await handle_groups(message)
        else:
            msg, markup = KeyboardConstructor.get_cluster_detail(cluster)
            await message.answer(msg, reply_markup=markup)
    except Exception as e:
        LOGGER.error(str(e))
    finally:
        handler.session.dispose()


async def add_group(message: types.Message, state: FSMContext):
    """Add new cluster"""
    if message.text == 'Cancel':
        await handle_cancel(message, state)

    else:
        handler = ClusterHandler()
        try:
            handler.add_cluster(message.from_user.id, message.text)
        except (NotExist, InvalidName) as e:
            await message.answer(str(e))
        else:
            buttons = KeyboardConstructor.get_base_reply_keyboard()
            await state.reset_state(with_data=True)
            await message.answer('Success', reply_markup=buttons)
        finally:
            handler.session.dispose()


async def handle_mute_cluster(callback: types.CallbackQuery):
    """Toggle mute/unmute cluster"""
    data = CallbackDataModel.parse_raw(callback.data)
    handler = ClusterHandler()
    try:
        cluster = handler.toggle_mute(data.id)
        if not cluster:
            await callback.answer('Cluster not exist')
            callback.message.from_user = callback.from_user
            await handle_groups(callback.message)
        else:
            msg, markup = KeyboardConstructor.get_cluster_detail(cluster)
            callback.message.text = 'cluster_{}'.format(data.id)
            await callback.message.edit_text(msg)
            await callback.message.edit_reply_markup(markup)
            await callback.answer('Success')
    except Exception as e:
        LOGGER.error(str(e))
    finally:
        handler.session.dispose()


async def handle_delete_cluster(callback: types.CallbackQuery):
    """Delete cluster"""
    data = CallbackDataModel.parse_raw(callback.data)
    handler = ClusterHandler()
    try:
        handler.delete_cluster(data.id)
    except NotExist:
        await callback.answer('')
        await callback.message.answer('Cluster not exist')
    else:
        await callback.answer('')
        await callback.message.answer('Success')
    finally:
        handler.session.dispose()
    callback.message.from_user = callback.from_user
    await handle_groups(callback.message)


async def handle_add_address(callback: types.CallbackQuery, state: FSMContext):
    """Add address to cluster"""
    data = CallbackDataModel.parse_raw(callback.data)
    blk = data.data.get('blk')
    await state.update_data(cluster_id=data.id)
    if blk:
        address = parse_message(callback.message.html_text)
        await state.set_state(AddAddressState.name)
        await state.update_data(wallet=address)
        await state.update_data(blockchain=blk)
        msg = 'Input name'
    else:
        await state.set_state(AddAddressState.wallet)
        msg = 'Input address'
    buttons = KeyboardConstructor.get_cancel_button()
    await callback.answer('')
    await callback.message.answer(msg, reply_markup=buttons)


async def handle_back_to_cluster(callback: types.CallbackQuery):
    """Handle back button for addresses list"""
    data = CallbackDataModel.parse_raw(callback.data)
    callback.message.text = f'cluster_{data.id}'
    await callback.answer('Back to cluster')
    await handle_cluster_detail(callback.message)
