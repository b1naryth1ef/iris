import logging
from collections import OrderedDict

from ..common.util import random_uuid
from ..common.identity import IdentityMixin
from ..data.base_pb2 import *
from .base import *

log = logging.getLogger(__name__)

class Shard(BaseModel):
    """
    Shards represent a divided section of the network that segments data,
    allowing overlying clients to provide a type of "board" or "sub-site"
    breakout. All other type of data apart from users is hierarcherly organized
    under a shard.
    """
    HASH_FIELDS = ['uid', 'name', 'desc', 'public', 'pow_load', 'pow_char', 'meta']

    uid = CharField(max_length=32, default=random_uuid)
    name = CharField(max_length=128)
    desc = CharField(max_length=2048)
    public = BooleanField(default=True)
    pow_load = IntegerField(default=3)
    pow_char = CharField(max_length=1, default='0')
    meta = BlobField()

    active = BooleanField(default=True)

    def get_pow(self):
        return ProofOfWork(load=self.pow_load, char=self.pow_char)

    def to_proto(self):
        shard = IShard()
        shard.id = self.id
        shard.uid = self.uid
        shard.name = self.name
        shard.desc = self.desc
        shard.public = self.public
        shard.pow_load = self.pow_load
        shard.pow_char = self.pow_char
        shard.meta = str(self.meta)
        return shard

    @classmethod
    def from_proto(cls, obj):
        return super(Shard, cls).from_proto(obj, cls(
            id=obj.id,
            uid=obj.uid,
            name=obj.name,
            desc=obj.desc,
            public=obj.public,
            pow_load=obj.pow_load,
            pow_char=obj.pow_char,
            meta=obj.meta,
            active=False))

