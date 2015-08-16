import logging

from datetime import datetime

from ..common.identity import IdentityMixin
from ..data.base_pb2 import *

from .base import *
from .proxies import ShardProxy

log = logging.getLogger(__name__)

class User(BaseModel, IdentityMixin, SignatureModel()):
    HASH_FIELDS = ['id', 'public_key', 'sign_key', 'nickname']

    public_key = BlobField()
    sign_key = BlobField()

    # User nickname. This doesn't need to be unique.
    nickname = CharField(max_length=128, null=True)

    # If true, we will never interact with this user
    blocked = BooleanField(default=False)

    # When did we first and last see them
    first_authed = DateTimeField(default=datetime.utcnow)
    last_authed = DateTimeField(default=datetime.utcnow)

    def to_proto(self):
        obj = IUser()
        obj.id = self.id
        obj.pubkey = self.public_key
        obj.signkey = self.sign_key
        obj.nickname = self.nickname
        obj.signature = self.signature
        assert(obj.id == self.hash)
        return obj

    @classmethod
    def from_proto(cls, obj):
        return super(User, cls).from_proto(obj, cls(
            id=obj.id,
            public_key=obj.pubkey,
            sign_key=obj.signkey,
            signature=obj.signature,
            nickname=obj.nickname))

    def add_connection(self, conn):
        host, port = conn

        conn, created = UserConn.get_or_create(
            user=self,
            host=host,
            port=port)

        conn.last_seen = datetime.utcnow()
        conn.conns += 1
        conn.save()

class UserSub(BaseModel):
    id = IntegerField(primary_key=True)

    user = ForeignKeyField(User)
    shard = ForeignKeyField(ShardProxy)
    active = BooleanField(default=True)

class UserConn(BaseModel):
    id = IntegerField(primary_key=True)

    user = ForeignKeyField(User)

    host = CharField(max_length=256)
    port = IntegerField()

    last_seen = DateTimeField(default=datetime.utcnow)
    conns = IntegerField(default=1)

