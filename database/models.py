"""Bot database models"""

from sqlalchemy import Column, BOOLEAN, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.mysql.types import VARCHAR, BIGINT, DATETIME, NUMERIC, SMALLINT, LONGTEXT, FLOAT, INTEGER
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """Bot user"""
    __tablename__ = "users"

    id = Column(BIGINT(unsigned=False), primary_key=True, autoincrement=False)
    created_at = Column(DATETIME)
    balance = Column(NUMERIC(precision=10, scale=2), nullable=False, default=0)
    notification_cost = Column(NUMERIC(precision=10, scale=2), nullable=False, default=1)
    notifications_remain = Column(BIGINT(unsigned=True), nullable=False)
    is_active = Column(BOOLEAN(create_constraint=True))

    clusters = relationship(
        'Cluster',
        back_populates='user',
        uselist=True
    )

    alerts = relationship(
        'AlertHistory',
        back_populates='user',
        uselist=True
    )

    def __str__(self) -> str:
        return '💵 Balance: {:.2f}\n💸 Notification Cost: {:.2f}\n' \
           '📳 Notification remain: {}\n📆 Registered: {}\nActive: {}'.format(
            self.balance,
            self.notification_cost,
            self.notifications_remain,
            self.created_at.strftime('%Y-%m-%d %H:%M:%S %Z'),
            f"{'✅' if self.is_active else '❌'}{self.is_active}"
        )


class Cluster(Base):
    """Cluster of addresses"""
    __tablename__ = 'clusters'

    id = Column(BIGINT(unsigned=True), primary_key=True)
    name = Column(VARCHAR(28), nullable=False)
    user_id = Column(BIGINT, ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'))
    chats = Column(LONGTEXT)
    watch = Column(BOOLEAN(create_constraint=True), default=True)

    addresses = relationship(
        'ClusterAddress',
        back_populates='cluster',
        uselist=True
    )
    user = relationship(
        User,
        back_populates='clusters',
        uselist=False
    )


class Blockchain(Base):
    """Blockchain"""
    __tablename__ = 'blockchains'
    id = Column(SMALLINT(unsigned=True), primary_key=True)
    title = Column(VARCHAR(127), unique=True, nullable=False)
    tag = Column(VARCHAR(10), unique=True, nullable=False)
    tx_link_template = Column(VARCHAR(255))
    explorer_link_template = Column(VARCHAR(255))
    explorer_title = Column(VARCHAR(255))

    addresses = relationship(
        'Address',
        back_populates='blockchain',
        uselist=True
    )


class Address(Base):
    """Address to track"""
    __tablename__ = "addresses"

    id = Column(BIGINT(unsigned=True), primary_key=True)
    wallet = Column(VARCHAR(100), nullable=False)
    blockchain_id = Column(
        SMALLINT(unsigned=True),
        ForeignKey('blockchains.id', ondelete='CASCADE', onupdate='CASCADE')
    )
    add_success = Column(BOOLEAN(create_constraint=True), default=True)

    constraint = UniqueConstraint(
        wallet, blockchain_id
    )

    blockchain = relationship(
        Blockchain,
        back_populates='addresses',
        uselist=False
    )

    clusters = relationship(
        'ClusterAddress',
        back_populates='address',
        uselist=True
    )


class ClusterAddress(Base):
    """Many-to-many table for addresses and clusters"""
    __tablename__ = 'clusters_addresses'

    id = Column(BIGINT(unsigned=True), primary_key=True)
    cluster_id = Column(BIGINT(unsigned=True), ForeignKey('clusters.id', ondelete='CASCADE', onupdate='CASCADE'))
    address_id = Column(BIGINT(unsigned=True), ForeignKey('addresses.id', ondelete='CASCADE', onupdate='CASCADE'))
    watch = Column(BOOLEAN(create_constraint=True))
    address_name = Column(VARCHAR(28), nullable=False)

    cluster = relationship(
        Cluster,
        back_populates='addresses',
        uselist=False
    )
    address = relationship(
        Address,
        back_populates='clusters',
        uselist=False
    )


class AlertHistory(Base):
    """Alert history"""
    __tablename__ = 'alert_history'
    id = Column(BIGINT(unsigned=True), primary_key=True)
    user_id = Column(BIGINT, ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'))
    blockchain = Column(VARCHAR(100), nullable=False)
    wallet = Column(VARCHAR(100), nullable=False)
    balance_delta = Column(NUMERIC(precision=10, scale=2), nullable=False)
    created_at = Column(DATETIME)

    user = relationship(
        User,
        back_populates='alerts',
        uselist=False
    )

class Transaction(Base):
    """Transaction for the graph"""
    __tablename__ = 'transactions'
    id = Column(BIGINT(unsigned=True), primary_key=True)
    wallet_1 = Column(VARCHAR(100), nullable=False)
    wallet_2 = Column(VARCHAR(100), nullable=False)
    blockchain = Column(VARCHAR(100), nullable=False)
    balance = Column(FLOAT(), nullable=False)
    date = Column(DATETIME)
    direction = Column(VARCHAR(100), nullable=False)
    token = Column(VARCHAR(100), nullable=False)
