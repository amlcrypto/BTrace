"""Bot handlers module"""
import datetime
import json
from typing import Tuple, List

from aiogram import types, Bot

from database.models import User, Cluster, Blockchain, ClusterAddress
from exceptions import NotExist
from handlers.database_handlers import AddressesHandler
from schema.bot_schema import CallbackDataModel
from schema.kafka_schema import Incoming, Transaction


class KeyboardConstructor:
    """Handler to create messages with keyboards or single keyboards"""
    @staticmethod
    def get_inline_button(text: str, action: str, data: int) -> types.InlineKeyboardButton:
        """InlineButton factory"""
        return types.InlineKeyboardButton(
            text=text,
            callback_data=CallbackDataModel(
                action=action,
                id=data
            ).json()
        )

    @classmethod
    def get_base_reply_keyboard(cls) -> types.ReplyKeyboardMarkup:
        """Returns base menu buttons"""
        profile = types.KeyboardButton('My profile')
        clusters = types.KeyboardButton('My clusters')
        add_cluster = types.KeyboardButton('Add cluster')
        help_button = types.KeyboardButton('Help')

        reply_buttons = types.ReplyKeyboardMarkup(
            [[profile, clusters, add_cluster, help_button]],
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
    def get_addresses_list(cls, cluster: Cluster) -> Tuple[str, types.InlineKeyboardMarkup]:
        """
        Get cluster and returns message with list of cluster addresses and inline keyboard
        :param cluster: Cluster
        :return: Tuple[str, InlineKeyboardMarkup]
        """
        msg = ['<b>Addresses:</b>']
        for link in cluster.addresses:
            row = f"{link.address.wallet[:5]}...{link.address.wallet[-5:]} /address_{link.id}"
            msg.append(row)

        markup = types.InlineKeyboardMarkup(inline_keyboard=[])
        buttons = []
        for text, action in (('Add address', 'add_address'), ('Back', 'back_to_cluster')):
            buttons.append(cls.get_inline_button(text, action, cluster.id))

        markup.inline_keyboard.append(buttons)
        return '\n'.join(msg), markup

    @classmethod
    def get_clusters_list(cls, user: User) -> str:
        """
        Get user and returns message contains list of user clusters
        :param user: User - BTrace client instance
        :return: str
        """
        msg = []
        for cluster in user.clusters:
            row = '{} ({}) /cluster_{}'.format(
                    cluster.name,
                    len(cluster.addresses),
                    cluster.id
                )
            msg.append(row)
        return '\n'.join(msg)

    @classmethod
    def get_address_detail(cls, address: ClusterAddress) -> Tuple[str, types.InlineKeyboardMarkup]:
        """Get address link and returns message and keyboard"""
        blockchain = AddressesHandler().get_blockchain_by_id(address.address.blockchain_id)

        msg = '<b>Address</b>:\n<code>{}</code>\n<a href="{}{}">' \
              'Watch on {}</a>\n<b>Name:</b> {}\n<b>Blockchain: </b>{}\n<b>Watching: </b>{}'.format(
                  address.address.wallet,
                  blockchain.explorer_link_template,
                  address.address.wallet,
                  blockchain.explorer_title,
                  address.address_name,
                  f"{blockchain.title} ({blockchain.tag})",
                  address.watch
              )
        buttons_data = [
            ('Rename', 'rename_address', address.id),
            ('Mute' if address.watch else 'Unmute', 'toggle_mute_address', address.id),
            ('Delete', 'delete_address', address.id),
            ('Back', 'view_addresses', address.cluster_id)
        ]
        markup = types.InlineKeyboardMarkup(inline_keyboard=[
            [cls.get_inline_button(*x) for x in buttons_data[:2]],
            [cls.get_inline_button(*x) for x in buttons_data[2:]]
        ])
        return msg, markup

    @classmethod
    def get_cluster_detail(cls, cluster: Cluster) -> Tuple[str, types.InlineKeyboardMarkup]:
        """Returns cluster detail message and inline keyboard"""
        msg = '<b>Name:</b>\n{}\n<b>Addresses count:</b> {}\n<b>Watching: </b>{}'.format(
            cluster.name,
            len(cluster.addresses),
            cluster.watch
        )
        buttons_data = [
            ('View addresses', 'view_addresses'),
            ('Add address', 'add_address'),
            ('Mute' if cluster.watch else 'Unmute', 'toggle_mute_cluster'),
            ('Rename', 'rename_cluster'),
            ('Delete', 'delete_cluster'),
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
    def format_transaction_message(
            cls,
            wallet: str,
            transaction: Transaction,
            blockchain: Blockchain,
            cluster: Cluster,
            name: str
    ) -> str:
        """Returns message for transaction"""
        src_name = ' ' + name if wallet == transaction.src else ''
        dst_name = ' ' + name if wallet == transaction.dst else ''
        msg = 'Cluster: {}\nBlockchain: {}\nSender: {}\nReceiver: {}\nVALUE: {:.2f} {}\nTIME (UTC): {}'.format(
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

    @classmethod
    async def handle_notification(cls, data: Incoming, bot: Bot):
        """Handle notification"""
        try:
            addresses_handler = AddressesHandler()

            address = addresses_handler.get_address_by_wallet_and_blockchain(
                wallet=data.wallet,
                blockchain=data.blockchain
            )
        except NotExist as e:
            return data
        else:
            links = addresses_handler.get_links_by_address_id(address.id)

            messages = []
            chats = []
            for transaction in data.transactions:
                for link in links:
                    messages.append(
                        cls.format_transaction_message(
                            wallet=data.wallet,
                            transaction=transaction,
                            blockchain=address.blockchain,
                            cluster=link.cluster,
                            name=link.address_name
                        )
                    )
                    link_chats = json.loads(link.cluster.chats)
                    chats.extend(link_chats)

            for msg in messages:
                for chat in set(chats):
                    await bot.send_message(chat_id=chat, text=msg, parse_mode='HTML', disable_web_page_preview=True)