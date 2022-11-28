"""Database handlers"""
import datetime
import json
from typing import Optional, List, Tuple

import pytz
from sqlalchemy import and_
from sqlalchemy.orm import joinedload, Session

from database.factory import DatabaseFactory
from database.models import User, Cluster, Address, Blockchain, ClusterAddress, AlertHistory
from exceptions import NotExist, InvalidName


class DatabaseHandler:
    """Database handler base class"""
    __db_name = None

    def __init__(self, name: str):
        self.session = DatabaseFactory.get_sync_engine(name)

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
        with Session(self.session) as sess:
            return sess.query(User).filter(
                User.id == user_id
            ).options(joinedload(User.clusters)).one_or_none()

    def add_user(self, user_id: int) -> User:
        """Save new user"""
        user = User(
            id=user_id,
            created_at=datetime.datetime.now(tz=pytz.UTC),
            balance=1000,
            notification_cost=1,
            notifications_remain=1000,
            is_active=True
        )
        with Session(self.session) as session:
            session.add(user)
            session.commit()
            session.refresh(user)
        return user

    def reduce_balance(self, user: User, blkchn: str, wallet: str) -> User:
        """Reduce user balance whet sent notification"""
        user.notifications_remain -= 1
        user.balance -= user.notification_cost
        alert_data = AlertHistory(
            user=user,
            blockchain=blkchn,
            wallet=wallet,
            balance_delta=user.notification_cost,
            created_at=datetime.datetime.now()
        )
        with Session(self.session) as session:
            session.add(alert_data)
            session.add(user)
            session.commit()
            session.refresh(user)
        return user

    def get_alert_history(self, user_id: int) -> List[AlertHistory]:
        """Returns list of alerts"""
        with Session(self.session) as session:
            return session.query(AlertHistory).filter(AlertHistory.user_id == user_id).all()


class ClusterHandler(DatabaseHandler):
    """Clusters database handlers"""
    __db_name = 'tracer'

    def __init__(self):
        super(ClusterHandler, self).__init__(self.__db_name)

    def add_cluster(self, user_id: int, name: str) -> int:
        """Add new cluster"""
        self.check_name(name)
        cluster = Cluster(
            name=name,
            user_id=user_id,
            chats=json.dumps([user_id])
        )
        with Session(self.session) as session:
            session.add(cluster)
            session.commit()
            session.refresh(cluster)
        return cluster.id

    def get_cluster_by_id(self, cluster_id: int) -> Cluster:
        """Get cluster by id"""
        with Session(self.session) as session:
            return session.query(Cluster).filter(Cluster.id == cluster_id).options(
                joinedload(Cluster.addresses)
            ).one_or_none()

    def rename_cluster(self, cluster_id: int, name: str) -> None:
        """Rename cluster"""
        self.check_name(name)
        with Session(self.session) as session:
            cluster: Cluster = session.query(Cluster).filter(
                Cluster.id == cluster_id
            ).one_or_none()
            if not cluster:
                raise NotExist(f'Cluster not exist')
            cluster.name = name
            session.add(cluster)
            session.commit()

    def toggle_mute(self, cluster_id: int) -> Cluster:
        """Toggle watch property for cluster by id"""
        with Session(self.session) as session:
            cluster: Cluster = session.query(Cluster).filter(
                Cluster.id == cluster_id
            ).one_or_none()
            if not cluster:
                raise NotExist(f'Cluster not exist')
            cluster.watch = not cluster.watch
            session.add(cluster)
            session.commit()
            session.refresh(cluster)
        return cluster

    def delete_cluster(self, cluster_id: int) -> None:
        """Delete cluster"""
        with Session(self.session) as session:
            cluster: Cluster = session.query(Cluster).filter(Cluster.id == cluster_id).one_or_none()
            if not cluster:
                raise NotExist(f'Cluster not exist')
            for link in cluster.addresses:
                session.delete(link)
            session.delete(cluster)
            session.commit()


class AddressesHandler(DatabaseHandler):
    """Addresses database handler"""

    __db_name = 'tracer'

    def __init__(self):
        super(AddressesHandler, self).__init__(self.__db_name)

    def get_added_count(self, ids: List[int]) -> int:
        """Returns count of addresses for cluster"""
        with Session(self.session) as session:
            return session.query(Address).filter(Address.id.in_(ids)).filter(
                Address.add_success.is_(True)
            ).count()

    def add_success(self, address: Address, cluster_id: int, state: bool) -> Tuple[str, List[str]]:
        """Set success add value"""
        address.add_success = state
        with Session(self.session) as session:
            session.add(address)
            session.commit()
            session.refresh(address)
            cluster = session.query(Cluster).filter(Cluster.id == cluster_id).first()
            chats = json.loads(cluster.chats)
        return cluster.name, chats

    def get_blockchains(self) -> List[Blockchain]:
        """Get list of exist blockchains"""
        with Session(self.session) as session:
            response = session.query(Blockchain).all()
            return [x for x in response]

    def get_blockchain_by_id(self, blockchain_id: int) -> Blockchain:
        with Session(self.session) as session:
            return session.query(Blockchain).get(blockchain_id)

    def get_address_by_id(self, address_id: int) -> ClusterAddress:
        """Get address by id and blockchain name"""
        with Session(self.session) as session:
            link: ClusterAddress = session.query(ClusterAddress).join(Cluster).options(
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
        with Session(self.session) as session:
            link: ClusterAddress = session.query(ClusterAddress).filter(ClusterAddress.id == address_id).one_or_none()
            if not link:
                return -1
            link.address_name = name
            session.add(link)
            session.commit()

    def get_address_by_wallet_and_blockchain(self, wallet: str, blockchain: int) -> Address:
        """Get address by wallet and blockchain"""
        with Session(self.session) as session:
            address = session.query(Address).options(
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

    def add_address(self, cluster_id: int, wallet: str, blockchain: int, name: str = None, auto: bool = False) -> None:
        """Add new address"""
        if name:
            self.check_name(name)
        with Session(self.session) as session:
            cluster = session.query(Cluster).filter(Cluster.id == cluster_id).one_or_none()
            if not cluster:
                raise NotExist('Cluster not exist')
            try:
                address = self.get_address_by_wallet_and_blockchain(wallet, blockchain)

            except NotExist:
                blockchain = session.query(Blockchain).filter(
                    Blockchain.id == blockchain
                ).one_or_none()
                if not blockchain:
                    raise NotExist('Blockchain {} not exist'.format(blockchain))

                address = Address(
                    wallet=wallet,
                    blockchain=blockchain,
                    add_success=auto
                )
            link = session.query(ClusterAddress).filter(
                and_(
                    ClusterAddress.address_id == address.id,
                    ClusterAddress.cluster_id == cluster_id
                )
            ).count()
            if not link:
                link = ClusterAddress(
                    address=address,
                    cluster=cluster,
                    watch=True,
                    address_name=name or f"{wallet[:7]}...{wallet[-7:]}"
                )
                session.add(link)
                session.commit()

    def toggle_mute_address(self, address_id: int) -> ClusterAddress:
        """Toggle mute/unmute"""
        with Session(self.session) as session:
            link: ClusterAddress = session.query(ClusterAddress).options(
                joinedload(ClusterAddress.address)
            ).filter(
                ClusterAddress.id == address_id
            ).one_or_none()
            if not link:
                raise NotExist('Address for this cluster not exist')

            link.watch = not link.watch
            session.add(link)
            session.commit()
            session.refresh(link)
            return link

    def delete_address(self, link_id: int) -> Tuple[int, bool]:
        """Delete address"""
        with Session(self.session) as session:
            link: ClusterAddress = session.query(ClusterAddress).filter(
                ClusterAddress.id == link_id
            ).one_or_none()
            if not link:
                raise NotExist('Link not exist')
            deleted = False
            cluster_id = link.cluster_id
            address_id = link.address_id
            session.delete(link)
            session.commit()
            address: Address = session.query(Address).options(
                joinedload(Address.blockchain)
            ).get(address_id)
            if not len(address.clusters):
                deleted = (address.wallet, address.blockchain.id)
                session.delete(address)
                session.commit()
            return cluster_id, deleted

    def get_links_by_address_id(self, address_id: int) -> List[ClusterAddress]:
        """Get cluster_addresses by address_id"""
        with Session(self.session) as session:
            return session.query(ClusterAddress).options(
                joinedload(ClusterAddress.cluster)
            ).filter(
                and_(
                    ClusterAddress.address_id == address_id,
                    ClusterAddress.watch == 1
                )
            ).all()
