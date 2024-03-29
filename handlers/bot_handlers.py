"""Bot handlers module"""
import csv
import datetime
import json
import math
from typing import Tuple, List

from aiogram import types, Bot
from sqlalchemy.orm import Session

from config import PATH
from database.factory import DatabaseFactory
from database.models import User, Cluster, Blockchain, ClusterAddress, Address, Transaction
from exceptions import NotExist
from handlers.database_handlers import AddressesHandler, ClusterHandler, UsersHandler, TransactionHandler
from logger import LOGGER
from schema.bot_schema import CallbackDataModel
from schema.kafka_schema import Incoming, Transaction
from exchange_and_bridge_controller import Controller
from graphs.graph import Graph
import time


class KeyboardConstructor:
    """Handler to create messages with keyboards or single keyboards"""
    _engine = DatabaseFactory.get_sync_engine('tracer')

    @classmethod
    def create_alert_history_report(cls, user_id: int) -> str:
        """Creates report for user alert history"""
        history = UsersHandler().get_alert_history(user_id)
        filename = f'{PATH}/history_{user_id}.csv'
        with open(filename, 'w', encoding='utf-8') as f:
            keys = ['Blockchain', 'Wallet', 'Balance delta', 'Date']
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for item in history:
                alert_data = f"{item.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC" if item.created_at else 'N/A'
                row = (
                    item.blockchain,
                    item.wallet,
                    '{:.2f}'.format(item.balance_delta),
                    alert_data
                )
                writer.writerow(dict(zip(keys, row)))
        return filename

    @staticmethod
    def get_inline_button(text: str, action: str, data: int, **kwargs) -> types.InlineKeyboardButton:
        """InlineButton factory"""
        return types.InlineKeyboardButton(
            text=text,
            callback_data=CallbackDataModel(
                action=action,
                id=data,
                data=kwargs
            ).json()
        )

    @classmethod
    def get_clusters_choices(cls, ids: List[Tuple[str, int]]) -> types.InlineKeyboardMarkup:
        markup = types.InlineKeyboardMarkup(inline_keyboard=[])
        markup.inline_keyboard.append(
            [cls.get_inline_button(
                name, 'choose_cluster', id_
            ) for name, id_ in ids]
        )
        return markup

    @classmethod
    def get_base_reply_keyboard(cls) -> types.ReplyKeyboardMarkup:
        """Returns base menu buttons"""
        profile = types.KeyboardButton('👤My profile')
        add_address = types.KeyboardButton('➕Add address')
        clusters = types.KeyboardButton('👥My clusters')
        add_cluster = types.KeyboardButton('🏷Add cluster')
        help_button = types.KeyboardButton('❓Help')

        reply_buttons = types.ReplyKeyboardMarkup(
            [[profile, add_address, clusters, add_cluster, help_button]],
            resize_keyboard=True
        )
        return reply_buttons

    @classmethod
    def get_cancel_button(cls) -> types.ReplyKeyboardMarkup:
        """Return keyboard with cancel button"""
        buttons = types.ReplyKeyboardMarkup(keyboard=[
            [types.KeyboardButton(text='Cancel')]
        ], resize_keyboard=True)
        return buttons

    @classmethod
    def get_addresses_list(
            cls, cluster: Cluster, page: int = None
       ) -> Tuple[str, types.InlineKeyboardMarkup]:
        """
        Get cluster and returns message with list of cluster addresses and inline keyboard
        :param cluster: Cluster
        :param page: int or None
        :return: Tuple[str, InlineKeyboardMarkup]
        """
        per_page = 20
        if not page:
            page = 1
        end = page * per_page
        start = end - per_page
        with Session(bind=cls._engine) as session:
            session.add(cluster)
            addresses = [x for x in cluster.addresses if x.address.add_success]
            pages = math.ceil(len(addresses) / per_page)
            msg = [f'🏠<b>Addresses: (page {page} of {pages})</b>']
            for link in addresses[start:end]:
                row = f"{link.address.wallet[:5]}...{link.address.wallet[-5:]} /address_{link.id}"
                msg.append(row)

        markup = types.InlineKeyboardMarkup(inline_keyboard=[])
        buttons = []
        for text, action in (('➕Add address', 'add_address'), ('🔙Back', 'back_to_cluster')):
            buttons.append(cls.get_inline_button(text, action, cluster.id))
        pagination = []
        if page > 1:
            pagination.append(cls.get_inline_button('⬅️Previous', 'view_addresses', cluster.id, page=page - 1))
        if page < pages:
            pagination.append(cls.get_inline_button('➡️Next', 'view_addresses', cluster.id, page=page + 1))

        markup.inline_keyboard.append(buttons)
        if pagination:
            markup.inline_keyboard.append(pagination)
        return '\n'.join(msg), markup

    @classmethod
    def get_clusters_list(cls, user: User) -> str:
        """
        Get user and returns message contains list of user clusters
        :param user: User - BTrace client instance
        :return: str
        """
        msg = []
        with Session(bind=cls._engine) as session:
            session.add(user)
            for cluster in user.clusters:
                ids = [x.address_id for x in cluster.addresses]
                len_addresses = AddressesHandler().get_added_count(ids)
                row = '{} ({}) /cluster_{}'.format(
                        cluster.name,
                        len_addresses,
                        cluster.id
                    )
                msg.append(row)
        return '\n'.join(msg)

    @classmethod
    def get_address_detail(cls, address: ClusterAddress) -> Tuple[str, types.InlineKeyboardMarkup]:
        """Get address link and returns message and keyboard"""
        blockchain = AddressesHandler().get_blockchain_by_id(address.address.blockchain_id)
        with Session(bind=cls._engine) as session:
            session.add(address)
            msg = '🏠<b>Address</b>:\n<code>{}</code>\n<a href="{}{}">' \
                'Watch on {}</a>\n🏷<b>Name:</b> {}\n🔗<b>Blockchain: </b>{}\n👀<b>Tracking: </b>{}'.format(
                    address.address.wallet,
                    blockchain.explorer_link_template,
                    address.address.wallet,
                    blockchain.explorer_title,
                    address.address_name,
                    f"{blockchain.title} ({blockchain.tag})",
                    f"{'✅' if address.watch else '❌'}{address.watch}"
                )
            buttons_data = [
                ('🏷Rename', 'rename_address', address.id),
                ('🔇Mute' if address.watch else '🔊Unmute', 'toggle_mute_address', address.id),
                ('🚫Delete', 'delete_address', address.id),
                ('🔙Back', 'view_addresses', address.cluster_id)
            ]
            markup = types.InlineKeyboardMarkup(inline_keyboard=[
                [cls.get_inline_button(*x) for x in buttons_data[:2]],
                [cls.get_inline_button(*x) for x in buttons_data[2:]]
            ])
        return msg, markup

    @classmethod
    def get_cluster_detail(cls, cluster: Cluster) -> Tuple[str, types.InlineKeyboardMarkup]:
        """Returns cluster detail message and inline keyboard"""
        with Session(bind=cls._engine) as session:
            session.add(cluster)
            ids = [x.address_id for x in cluster.addresses]
            msg = '🏷<b>Name:</b>{}\n🔢<b>Addresses count:</b> {}\n👀<b>Tracking: </b>{}'.format(
                cluster.name,
                AddressesHandler().get_added_count(ids),
                f"{'✅'if cluster.watch else '❌'}{cluster.watch}"
            )
            buttons_data = [
                ('👁‍🗨View addresses', 'view_addresses'),
                ('➕Add address', 'add_address'),
                ('🔇Mute' if cluster.watch else '🔊Unmute', 'toggle_mute_cluster'),
                ('🏷Rename', 'rename_cluster'),
                ('🚫Delete', 'delete_cluster'),
            ]
            markup = types.InlineKeyboardMarkup(inline_keyboard=[
                [cls.get_inline_button(x, y, cluster.id) for x, y in buttons_data[:3]],
                [cls.get_inline_button(x, y, cluster.id) for x, y in buttons_data[3:]]
            ])
        return msg, markup

    @classmethod
    def get_blockchains_choices(cls, blockchains: List[Blockchain]) -> types.InlineKeyboardMarkup:
        """Returns inline keyboard to choose blockchain"""
        markup = types.InlineKeyboardMarkup(inline_keyboard=[])
        buttons = []
        for item in blockchains:
            button = cls.get_inline_button(
                text=f"{item.title} ({item.tag})",
                action='blockchain_choice',
                data=item.id
            )
            buttons.append(button)
        markup.inline_keyboard.append(buttons)
        return markup


class NotificationHandler:

    @staticmethod
    def get_link(href: str, verbose: str) -> str:
        """Returns link to message"""
        return '<a href="{}">{}</a>'.format(
            href,
            verbose
        )

    @classmethod
    async def format_transaction_message(
            cls,
            tx_hash: str,
            wallet: str,
            transaction: Transaction,
            blockchain: Blockchain,
            cluster: Cluster,
            name: str,
    ) -> str:
        """Returns message for transaction"""
        src_name = ' ' + name if wallet == transaction.src else ''
        dst_name = ' ' + name if wallet == transaction.dst else ''
        tx_link = blockchain.tx_link_template
        if tx_hash and tx_link:
            tx_link += tx_hash
        msg = '📍Transaction: {}\n🔒Cluster: {}\n🔗Blockchain: {}\n📤Sender: {}\n📥Receiver: {}\n💰VALUE: {:.2f} {}\n⏱TIME (UTC): {}'.format(
            cls.get_link(tx_link, 'Watch on ' + blockchain.explorer_title),
            cluster.name,
            f"{blockchain.title} ({blockchain.tag})",
            cls.get_link(
                blockchain.explorer_link_template + transaction.src,
                f'{transaction.src[:5]}...{transaction.src[-5:]}{src_name}'
            ),
            cls.get_link(
                blockchain.explorer_link_template + transaction.dst,
                f'{transaction.dst[:5]}...{transaction.dst[-5:]}{dst_name}'
            ),
            transaction.value,
            transaction.token,
            datetime.datetime.fromtimestamp(transaction.created_at).strftime(
                '%b %d, %Y, %H:%M:%S'
            )
        )
        return msg

    @staticmethod
    def get_auto_add_message(wallets: List[str], blockchain: str, name: str) -> str:
        """Create message about auto added addresses"""
        msg = ['<b>Automatically added to cluster {}:</b>'.format(name)]
        for wallet in set(wallets):
            msg.append('{} ({})\n'.format(
                f"{wallet[:5]}...{wallet[-5:]}",
                blockchain
            ))
        return '\n'.join(msg)

    @classmethod
    async def alert(cls, address: Address, data: Incoming, bot: Bot, addresses_handler: AddressesHandler):
        """Handle alert incoming message"""
        session = DatabaseFactory.get_sync_session('tracer')
        users_handler = UsersHandler()
        try:
            links = addresses_handler.get_links_by_address_id(address.id)

            for link in links:
                link_chats = json.loads(link.cluster.chats)

                user = users_handler.get_user_by_id(link.cluster.user_id)

                send_allowed = all([link.watch, user.is_active, user.notifications_remain,
                                    link.cluster.watch])
                if send_allowed:
                    session.add(link.cluster)
                    addresses = set(x.address for x in link.cluster.addresses)
                    for transaction in data.transactions:
                        msg = await cls.format_transaction_message(
                            tx_hash=transaction.tx_hash,
                            wallet=data.wallet,
                            transaction=transaction,
                            blockchain=address.blockchain,
                            cluster=link.cluster,
                            name=link.address_name
                        )
                        markup = types.InlineKeyboardMarkup(inline_keyboard=[])
                        if transaction.dst not in addresses:
                            button = KeyboardConstructor.get_inline_button(
                                text='➕Add address to trace',
                                action='add_address',
                                data=link.cluster_id,
                                blk=address.blockchain_id
                            )
                            markup.inline_keyboard.append([button])
                        gr = Graph()
                        for chat in link_chats:
                            now = gr.draw_graph(data.wallet, user.id ,user.created_at, transaction.created_at )
                            photo = open(f'{PATH}/graphs/img/{user.id}-{transaction.created_at}-{now}.jpg', 'rb')
                            # SVG/GIF
                            #first transaction -> another colors
                            await bot.send_photo(chat_id=chat, caption = msg, parse_mode='HTML', reply_markup=markup,
                            photo=photo)
                        user = users_handler.reduce_balance(user, address.blockchain.title, data.wallet)

        except Exception as e:
            LOGGER.error(str(e))
        finally:
            session.close_all()
            users_handler.session.dispose()

    @classmethod
    async def report(cls, address: Address, data: Incoming, bot: Bot, addresses_handler: AddressesHandler):
        """Handle report"""

        if data.action == 'add_address':
            if data.state == 1:
                result = 'added to tracing'
                try:
                    name, chats = addresses_handler.add_success(address, data.cluster_id, True)
                except Exception as e:
                    LOGGER.error(str(e))
                    return
            else:
                result = 'If something goes wrong, please contact administration'
                try:
                    cluster = ClusterHandler().get_cluster_by_id(data.cluster_id)
                except Exception as e:
                    LOGGER.error(str(e))
                    return
                chats = json.loads(cluster.chats)
                name = cluster.name
            try:
                blockchain = addresses_handler.get_blockchain_by_id(data.blockchain)
            except Exception as e:
                LOGGER.error(str(e))
            else:
                for chat in chats:
                    try:
                        await bot.send_message(
                            chat_id=chat,
                            text=f'{name}:\n{data.wallet[:5]}...{data.wallet[-5:]} ({blockchain.tag})\n{result}'
                        )
                    except Exception as e:
                        LOGGER.error(str(e))

    @classmethod
    async def handle_notification(cls, data: Incoming, bot: Bot, addresses_handler: AddressesHandler):
        """Handle notification"""
        # addresses_handler = AddressesHandler()
        try:
            address = addresses_handler.get_address_by_wallet_and_blockchain(
                wallet=data.wallet,
                blockchain=data.blockchain
            )
        except NotExist:
            return data
        except Exception as e:
            LOGGER.error(str(e))
        else:
            if data.action == 'alert':
                # add new trx in tracer.transactions
                tr_handler = TransactionHandler()
                # compare address with data.transaction. Maybe you shoud use for circle
                LOGGER.info(f'address: {address}, data: {data}, bot: {bot}, addresses_handler: {addresses_handler}')
                transaction_list = []
                for transaction in data.transactions:
                    data_new = {}
                    data_new['wallet_1'] = transaction.src
                    data_new['wallet_2'] = transaction.dst
                    data_new['blockchain'] = data.blockchain
                    data_new['direction'] = ''
                    data_new['balance'] = transaction.value
                    data_new['token'] = transaction.token
                    data_new['date'] = transaction.created_at
                    transaction_list.append(data_new)
                tr_handler.add_transaction(transaction_list)
                handler = cls.alert
            else:
                handler = cls.report
            await handler(address, data, bot, addresses_handler)
        # finally:
            # addresses_handler.session.dispose()

        # LOGGER.info(f'transaction.dst: {transaction.dst}')
        # src_name = ' '
        # alert = ''
        # dest_name = ''
        # if (wallet == transaction.src):
        #     src_name += name

        #     controller = Controller()
        #     #add check DEX, CEX, bridge address
        #     status = await controller.check_wallet(transaction.dst, blockchain.title)
        #     LOGGER.info('status:{}'.format(str(status)))
        #     if (status[0] == "SIMPLE_ADDRESS"):
        #         pass
        #     elif (status[0] == "BRIDGE"):
        #         alert = '\n 🔥 ALARM: This address has transferred funds to the bridge!\nNext, we will send the output transaction in another blockchain. '
        #         dest_name = status[1]
        #     elif (status[0] == "DEX"):
        #         alert = '\n 🔥 ALARM: This address sent funds to DEX.'
        #         dest_name = status[1]
        #     elif (status[0] == "CEX"):
        #         alert = '\n 🔥 ALARM: This address sent funds to CEX.'
        #         dest_name = status[1]
        #     elif (status[0] == "FARMING"):
        #         alert = '\n 🔥 ALARM: This address sent funds to Farming pool.'
        #         dest_name = status[1]

        # dst_name = ' ' + name if wallet == transaction.dst else ''