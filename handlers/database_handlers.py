"""Database handlers"""
import datetime
import json
from typing import Optional, List

import pytz
from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from database.factory import DatabaseFactory
from database.models import User, Cluster, Address, Blockchain, ClusterAddress
from exceptions import NotExist


class DatabaseHandler:
    """Database handler base class"""
    __db_name = None

    def __init__(self, name: str):
        self.session = DatabaseFactory.get_sync_session(name)

    def __del__(self):
        self.session.close()

    @staticmethod
    def check_name(name: str) -> bool:
        """Validate name"""
        if not name or len(name) > 28:
            return False
        return True


class UsersHandler(DatabaseHandler):
    """Users database handler"""
    __db_name = 'tracer'

    def __init__(self):
        super(UsersHandler, self).__init__(self.__db_name)

    def get_user_by_id(self, user_id: int) -> User:
        """Get bot user by user id"""
        return self.session.query(User).filter(
            User.id == user_id
        ).one_or_none()

    def add_user(self, user_id: int) -> User:
        """Save new user"""
        user = User(
            id=user_id,
            created_at=datetime.datetime.now(tz=pytz.UTC),
            balance=0,
            is_active=True
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user


class ClusterHandler(DatabaseHandler):
    """Clusters database handlers"""
    __db_name = 'tracer'

    def __init__(self):
        super(ClusterHandler, self).__init__(self.__db_name)

    def add_cluster(self, user_id: int, name: str) -> Optional[int]:
        """Add new cluster"""
        if self.check_name(name):
            cluster = Cluster(
                name=name,
                user_id=user_id,
                chats=json.dumps([user_id])
            )
            self.session.add(cluster)
            self.session.commit()
        else:
            return -1

    def get_cluster_by_id(self, cluster_id: int) -> Cluster:
        """Get cluster by id"""
        return self.session.query(Cluster).filter(Cluster.id == cluster_id).one_or_none()

    def rename_cluster(self, cluster_id: int, name: str) -> Optional[int]:
        """Rename cluster"""
        if self.check_name(name):
            cluster: Cluster = self.session.query(Cluster).filter(
                Cluster.id == cluster_id
            ).one_or_none()
            if not cluster:
                raise NotExist(f'Cluster not exist')
            cluster.name = name
            self.session.add(cluster)
            self.session.commit()
        else:
            return -1

    def toggle_mute(self, cluster_id: int) -> Cluster:
        """Toggle watch property for cluster by id"""
        cluster: Cluster = self.session.query(Cluster).filter(
            Cluster.id == cluster_id
        ).one_or_none()
        if not cluster:
            raise NotExist(f'Cluster not exist')
        cluster.watch = not cluster.watch
        self.session.add(cluster)
        self.session.commit()
        self.session.refresh(cluster)
        return cluster

    def delete_cluster(self, cluster_id: int) -> None:
        """Delete cluster"""
        cluster: Cluster = self.session.query(Cluster).filter(Cluster.id == cluster_id).one_or_none()
        if not cluster:
            raise NotExist(f'Cluster not exist')
        for link in cluster.addresses:
            self.session.delete(link)
        self.session.delete(cluster)
        self.session.commit()


class AddressesHandler(DatabaseHandler):
    """Addresses database handler"""

    __db_name = 'tracer'

    def __init__(self):
        super(AddressesHandler, self).__init__(self.__db_name)

    def get_blockchains(self) -> List[Blockchain]:
        """Get list of exist blockchains"""
        response = self.session.query(Blockchain).all()
        return [x for x in response]

    def get_blockchain_by_id(self, blockchain_id: int) -> Blockchain:
        return self.session.query(Blockchain).get(blockchain_id)

    def get_address_by_id(self, address_id: int) -> ClusterAddress:
        """Get address by id and blockchain name"""
        link: ClusterAddress = self.session.query(ClusterAddress).join(Cluster).options(
            joinedload(ClusterAddress.address)
        ).filter(
            ClusterAddress.id == address_id
        ).one_or_none()
        if not link:
            raise NotExist('Address not exist')
        return link

    def rename_address(self, address_id: int, name: str) -> Optional[int]:
        """Rename address"""
        link: ClusterAddress = self.session.query(ClusterAddress).filter(ClusterAddress.id == address_id).one_or_none()
        if not link:
            return -1
        link.address_name = name
        self.session.add(link)
        self.session.commit()

    def get_address_by_wallet_and_blockchain(self, wallet: str, blockchain: int) -> Address:
        """Get address by wallet and blockchain"""
        address = self.session.query(Address).filter(
            and_(
                Address.wallet == wallet,
                Address.blockchain_id == blockchain
            )
        ).one_or_none()
        if not address:
            raise NotExist('Address not exist')
        return address

    def add_address(self, cluster_id: int, wallet: str, blockchain: int, name: str = None) -> None:
        """Add new address"""
        cluster = self.session.query(Cluster).filter(Cluster.id == cluster_id).one_or_none()
        if not cluster:
            raise NotExist('Cluster not exist')
        try:
            address = self.get_address_by_wallet_and_blockchain(wallet, blockchain)

        except NotExist:
            blockchain = self.session.query(Blockchain).filter(
                Blockchain.id == blockchain
            ).one_or_none()
            if not blockchain:
                raise NotExist('Blockchain {} not exist'.format(blockchain))

            address = Address(
                wallet=wallet,
                blockchain=blockchain
            )
        link = ClusterAddress(
            address=address,
            cluster=cluster,
            watch=True,
            address_name=name or f"{wallet[:7]}...{wallet[-7:]}"
        )
        self.session.add(link)
        self.session.commit()

    def toggle_mute_address(self, address_id: int) -> ClusterAddress:
        """Toggle mute/unmute"""
        link: ClusterAddress = self.session.query(ClusterAddress).options(
            joinedload(ClusterAddress.address)
        ).filter(
            ClusterAddress.id == address_id
        ).one_or_none()
        if not link:
            raise NotExist('Address for this cluster not exist')

        link.watch = not link.watch
        self.session.add(link)
        self.session.commit()
        self.session.refresh(link)
        return link

    def delete_address(self, link_id: int) -> int:
        """Delete address"""
        link: ClusterAddress = self.session.query(ClusterAddress).filter(
            ClusterAddress.id == link_id
        ).one_or_none()
        if not link:
            raise NotExist('Link not exist')
        cluster_id = link.cluster_id
        address_id = link.address_id
        self.session.delete(link)
        self.session.commit()
        address: Address = self.session.query(Address).get(address_id)
        if not len(address.clusters):
            self.session.delete(address)
            self.session.commit()
        return cluster_id
