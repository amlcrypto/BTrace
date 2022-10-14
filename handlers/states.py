"""Module with states"""
from aiogram.dispatcher.filters.state import State, StatesGroup


class AddClusterState(StatesGroup):
    """State for add new cluster"""
    cluster_name = State()


class AddAddressState(StatesGroup):
    """State for add address"""
    wallet = State()
    blockchain = State()
    name = State()


class RenameClusterState(StatesGroup):
    """State for rename cluster"""
    cluster_name = State()


class RenameAddressState(StatesGroup):
    """State for rename address"""
    address_name = State()
