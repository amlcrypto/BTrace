"""Bot database models"""

from sqlalchemy import Column, BOOLEAN, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.mysql.types import VARCHAR, BIGINT, DATETIME, NUMERIC, SMALLINT, LONGTEXT
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class User(Base):
    """Bot user"""
    __tablename__ = "users"

    id = Column(BIGINT(unsigned=False), primary_key=True, autoincrement=False)
    created_at = Column(DATETIME)
    balance = Column(NUMERIC(precision=2, asdecimal=True), nullable=False, default=0)
    is_active = Column(BOOLEAN(create_constraint=True))

    clusters = relationship(
        'Cluster',
        back_populates='user',
        uselist=True
    )

    def __str__(self) -> str:
        return 'Balance: {:.2f}\nRegistered: {}\nActive: {}'.format(
            self.balance,
            self.created_at.strftime('%Y-%m-%d %H:%M:%S %Z'),
            self.is_active
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
