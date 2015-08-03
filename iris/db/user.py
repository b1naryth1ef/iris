import logging

from datetime import datetime

from ..common.identity import IdentityMixin
from ..data.base_pb2 import *

from .base import *

log = logging.getLogger(__name__)

class User(BaseModel, IdentityMixin):
    HASH_FIELDS = ['id', 'public_key', 'nickname']

    public_key = BlobField()

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
        obj.pubkey = str(self.public_key).encode('hex')
        obj.nickname = self.nickname
        obj.first_authed = self.first_authed.strftime('%s')
        obj.last_authed = self.last_authed.strftime('%s')
        return obj

    @classmethod
    def from_proto(cls, obj):
        return super(User, cls).from_proto(obj, cls(
            id=obj.id,
            public_key=obj.pubkey.decode('hex'),
            nickname=obj.nickname))


