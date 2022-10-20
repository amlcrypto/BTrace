"""Database handlers"""
import datetime
import json
from typing import Optional, List, Tuple

import pytz
from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from database.factory import DatabaseFactory
from database.models import User, Cluster, Address, Blockchain, ClusterAddress, AlertHistory
from exceptions import NotExist, InvalidName


class DatabaseHandler:
    """Database handler base class"""
    __db_name = None

    def __init__(self, name: str):
        self.session = DatabaseFactory.get_sync_session(name)

    def __del__(self):
        self.session.close()

    @staticmethod
    def check_name(name: str) -> None:
        """Validate name"""
        if not name or len(name) > 28:
            raise InvalidName('Name too long (max 28 char)')


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

    def reduce_balance(self, user: User, blkchn: str, wallet: str) -> User:
        """Reduce user balance whet sent notification"""
        user.notifications_remain -= 1
        user.balance -= user.notification_cost
        alert_data = AlertHistory(
            user=user,
            blockchain=blkchn,
            wallet=wallet,
            balance_delta=user.notification_cost
        )
        self.session.add(alert_data)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user


class ClusterHandler(DatabaseHandler):
    """Clusters database handlers"""
    __db_name = 'tracer'

    def __init__(self):
        super(ClusterHandler, self).__init__(self.__db_name)

    def add_cluster(self, user_id: int, name: str) -> None:
        """Add new cluster"""
        self.check_name(name)
        cluster = Cluster(
            name=name,
            user_id=user_id,
            chats=json.dumps([user_id])
        )
        self.session.add(cluster)
        self.session.commit()

    def get_cluster_by_id(self, cluster_id: int) -> Cluster:
        """Get cluster by id"""
        return self.session.query(Cluster).filter(Cluster.id == cluster_id).options(
            joinedload(Cluster.addresses)
        ).one_or_none()

    def rename_cluster(self, cluster_id: int, name: str) -> None:
        """Rename cluster"""
        self.check_name(name)
        cluster: Cluster = self.session.query(Cluster).filter(
            Cluster.id == cluster_id
        ).one_or_none()
        if not cluster:
            raise NotExist(f'Cluster not exist')
        cluster.name = name
        self.session.add(cluster)
        self.session.commit()

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

    def get_added_count(self, ids: List[int]) -> int:
        """Returns count of addresses for cluster"""
        return self.session.query(Address).filter(Address.id.in_(ids)).filter(
            Address.add_success.is_(True)
        ).count()

    def add_success(self, address: Address, cluster_id: int, state: bool) -> Tuple[str, List[str]]:
        """Set success add value"""
        address.add_success = state
        self.session.add(address)
        self.session.commit()
        self.session.refresh(address)
        cluster = self.session.query(Cluster).filter(Cluster.id == cluster_id).first()
        chats = json.loads(cluster.chats)
        return cluster.name, chats

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
        self.check_name(name)
        link: ClusterAddress = self.session.query(ClusterAddress).filter(ClusterAddress.id == address_id).one_or_none()
        if not link:
            return -1
        link.address_name = name
        self.session.add(link)
        self.session.commit()

    def get_address_by_wallet_and_blockchain(self, wallet: str, blockchain: int) -> Address:
        """Get address by wallet and blockchain"""
        address = self.session.query(Address).options(
            joinedload(Address.blockchain)
        ).filter(
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
        if name:
            self.check_name(name)

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
                blockchain=blockchain,
                add_success=False
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

    def delete_address(self, link_id: int) -> Tuple[int, bool]:
        """Delete address"""
        link: ClusterAddress = self.session.query(ClusterAddress).filter(
            ClusterAddress.id == link_id
        ).one_or_none()
        if not link:
            raise NotExist('Link not exist')
        deleted = False
        cluster_id = link.cluster_id
        address_id = link.address_id
        self.session.delete(link)
        self.session.commit()
        address: Address = self.session.query(Address).options(
            joinedload(Address.blockchain)
        ).get(address_id)
        if not len(address.clusters):
            deleted = (address.wallet, address.blockchain.id)
            self.session.delete(address)
            self.session.commit()
        return cluster_id, deleted

    def get_links_by_address_id(self, address_id: int) -> List[ClusterAddress]:
        """Get cluster_addresses by address_id"""
        return self.session.query(ClusterAddress).options(
            joinedload(ClusterAddress.cluster)
        ).filter(
            and_(
                ClusterAddress.address_id == address_id,
                ClusterAddress.watch == 1
            )
        ).all()
