import time

from ..common.util import random_uuid

from .base import *
from .user import User
from .entry import Entry

class Block(BaseModel, SignatureModel('solver')):
    HASH_FIELDS = ['uid', 'parent', 'solver', 'time', 'position', 'initial', 'entries']

    uid = CharField(max_length=32, default=random_uuid)
    parent = ForeignKeyField('self', null=True)
    solver = ForeignKeyField(User)
    time = IntegerField(default=time.time)

    # The position of this block, as text so we can go forever!
    position = TextField()

    # True if this is the first block in a chain.
    initial = BooleanField(default=False)

    # Utility only, blocks are never bound to a single shard
    shard_id = CharField(max_length=64, null=True)

    # Proof of work "salt"
    proof = IntegerField()

    @property
    def shard(self):
        from .shard import Shard
        return Shard.get(Shard.id == self.shard)

class BlockEntry(BaseModel):
    block = ForeignKeyField(Block, 'entries')
    entry = ForeignKeyField(Entry, 'block')
