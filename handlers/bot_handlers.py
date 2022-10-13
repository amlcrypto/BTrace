"""Bot handlers module"""
from typing import Tuple, List

from aiogram import types

from database.models import User, Cluster, Blockchain
from schema.bot_schema import CallbackDataModel


class KeyboardConstructor:

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
        buttons = types.ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)
        button = types.KeyboardButton(text='Cancel')
        buttons.keyboard.append([button])
        return buttons

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
    def get_cluster_detail(cls, cluster: Cluster) -> Tuple[str, types.InlineKeyboardMarkup]:
        """Returns cluster detail message and inline keyboard"""
        msg = '<b>Name:</b>\n{}\n<b>Addresses count:</b> {}\n<b>Watching: </b>{}'.format(
            cluster.name,
            len(cluster.addresses),
            cluster.watch
        )
        markup = types.InlineKeyboardMarkup(inline_keyboard=[])
        markup.inline_keyboard.append([
            types.InlineKeyboardButton(
                text='View addresses',
                callback_data=CallbackDataModel(action='view_addresses', id=cluster.id).json()
            ),
            types.InlineKeyboardButton(
                text='Add address',
                callback_data=CallbackDataModel(action='add_address', id=cluster.id).json()
            ),
            types.InlineKeyboardButton(
                text='Mute' if cluster.watch else 'Unmute',
                callback_data=CallbackDataModel(action='toggle_mute_cluster', id=cluster.id).json()
            )
        ])
        markup.inline_keyboard.append([
            types.InlineKeyboardButton(
                text='Rename',
                callback_data=CallbackDataModel(action='rename_cluster', id=cluster.id).json()
            ),
            types.InlineKeyboardButton(
                text='Delete',
                callback_data=CallbackDataModel(action='delete_cluster', id=cluster.id).json()
            )
        ])
        return msg, markup

    @classmethod
    def get_blockchains_choices(cls, blockchains: List[Blockchain]) -> types.InlineKeyboardMarkup:
        """Returns inline keyboard to choose blockchain"""
        markup = types.InlineKeyboardMarkup(inline_keyboard=[])
        buttons = []
        for item in blockchains:
            button = types.InlineKeyboardButton(
                text=f"{item.title} ({item.tag})",
                callback_data=CallbackDataModel(
                    action='blockchain_choice',
                    id=item.id
                ).json()
            )
            buttons.append(button)
        markup.inline_keyboard.append(buttons)
        return markup
