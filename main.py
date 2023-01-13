import asyncio

from aiogram.bot.bot import Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Command

from callbacks.addresses import get_address, get_blockchain, get_name, handle_address_detail, \
    handle_rename_address, handle_rename_address_set_name, handle_mute_address, handle_delete_address
from callbacks.base import handle_cancel, handle_start
from callbacks.clusters import handle_cluster_detail, add_group, handle_rename_cluster_set_name, \
    handle_rename_cluster, handle_view_cluster_addresses, handle_mute_cluster, handle_delete_cluster, \
    handle_add_address, handle_back_to_cluster
from callbacks.main_menu import handle_help, handle_profile, handle_groups, handle_group_add, \
    handle_alert_history_csv, handle_choose_cluster, handle_add_address_main
from config import settings
from handlers.kafka_handlers import consume_data
from handlers.handler_filters import CallbackDataActionFilter
from handlers.states import AddClusterState, RenameClusterState, AddAddressState, RenameAddressState

bot = Bot(token=settings.TOKEN, parse_mode='HTML',disable_web_page_preview=True)

storage = MemoryStorage()
disp = Dispatcher(bot=bot, storage=storage)

disp.register_message_handler(handle_cancel, lambda x: x.text == 'Cancel')
disp.register_message_handler(handle_start, Command(commands=['start'], prefixes='/'))
disp.register_message_handler(handle_help, lambda x: x.text == '❓Help')
disp.register_message_handler(handle_add_address_main, lambda x: x.text == '➕Add address')
disp.register_callback_query_handler(handle_choose_cluster, CallbackDataActionFilter(action='choose_cluster'))
disp.register_message_handler(handle_profile, lambda x: x.text == '👤My profile')
disp.register_callback_query_handler(handle_alert_history_csv, CallbackDataActionFilter(action='alert_history'))
disp.register_message_handler(handle_groups, lambda x: x.text == '👥My clusters')
disp.register_message_handler(handle_group_add, lambda x: x.text == '🏷Add cluster')
disp.register_message_handler(handle_cluster_detail, regexp=r'/cluster_\d+')
disp.register_message_handler(add_group, state=AddClusterState.cluster_name)
disp.register_message_handler(handle_rename_cluster_set_name, state=RenameClusterState.cluster_name)
disp.register_callback_query_handler(handle_rename_cluster, CallbackDataActionFilter(action='rename_cluster'))
disp.register_callback_query_handler(handle_view_cluster_addresses, CallbackDataActionFilter(action='view_addresses'))
disp.register_callback_query_handler(handle_mute_cluster, CallbackDataActionFilter(action='toggle_mute_cluster'))
disp.register_callback_query_handler(handle_delete_cluster, CallbackDataActionFilter(action='delete_cluster'))
disp.register_callback_query_handler(handle_add_address, CallbackDataActionFilter(action='add_address'))
disp.register_callback_query_handler(handle_back_to_cluster, CallbackDataActionFilter(action='back_to_cluster'))
disp.register_message_handler(get_address, state=AddAddressState.wallet)
disp.register_callback_query_handler(get_blockchain, state=AddAddressState.blockchain)
disp.register_message_handler(get_blockchain, state=AddAddressState.blockchain)
disp.register_message_handler(get_name, state=AddAddressState.name)
disp.register_message_handler(handle_address_detail, regexp=r'/address_\d+')
disp.register_callback_query_handler(handle_rename_address, CallbackDataActionFilter(action='rename_address'))
disp.register_message_handler(handle_rename_address_set_name, state=RenameAddressState.address_name)
disp.register_callback_query_handler(handle_mute_address, CallbackDataActionFilter(action='toggle_mute_address'))
disp.register_callback_query_handler(handle_delete_address, CallbackDataActionFilter(action='delete_address'))


async def main():
    try:
        await asyncio.gather(
            disp.start_polling(disp),
            consume_data(bot)
        )
    finally:
        disp.stop_polling()


if __name__ == '__main__':
    asyncio.run(main())
