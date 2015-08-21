import logging
from collections import OrderedDict

from ..client.chain import Chain

from ..common.effort import EffortCalculator
from ..common.pow import ProofOfWork
from ..common.util import random_uuid
from ..common.identity import IdentityMixin
from ..data.base_pb2 import *

from .base import *
from .block import Block
from .proxies import ShardProxy


log = logging.getLogger(__name__)

class Shard(BaseModel):
    """
    Shards represent a divided section of the network that segments data,
    allowing overlying clients to provide a type of "board" or "sub-site"
    breakout. All other type of data apart from users is hierarcherly organized
    under a shard.
    """
    HASH_FIELDS = ['uid', 'name', 'desc', 'public', 'meta', 'initial']

    uid = CharField(max_length=32, default=random_uuid)
    name = CharField(max_length=128)
    desc = CharField(max_length=2048)

    # If false, we won't ever broadcast we have this, unless somemone has the ID
    public = BooleanField(default=True)

    # Meta is whatever the hell the implementation wants (generally JSON)
    meta = BlobField()

    # Link to the initial block in the chain
    initial = ForeignKeyField(Block)

    # If false, we won't sync or broadcast this shard
    active = BooleanField(default=True)

    def get_chain_length(self):
        """
        Returns the current length of the chain
        """
        return Block.select().where(
            (Block.shard == self.shard.id) &
            (Block.commited == True)).count()

    def get_block_at(self, index):
        """
        Returns a block in the chain at a specific index
        """
        # If we're negative, start from the front of the chain
        if index < 0:
            index = self.get_chain_length() + index

        return Block.get(
            (Block.shard == self.shard.id) &
            (Block.commited == True) &
            (Block.position == str(index)))

    def get_chain(self):
        return Chain(self)

    def get_last_block(self):
        try:
            return Block.get((Block.parent >> None) & (Block.initial == False) & (Block.commited == True))
        except Block.DoesNotExist:
            return self.initial

    def get_pow(self, obj):
        return ProofOfWork(load=EffortCalculator(self).calculate(obj))

    def get_block_pow(self, block):
        calc = EffortCalculator(self)
        return ProofOfWork(load=calc.calculate(block))

    def to_proto(self):
        shard = IShard()
        shard.id = self.id
        shard.uid = self.uid
        shard.name = self.name
        shard.desc = self.desc
        shard.public = self.public
        shard.meta = self.meta
        shard.initial.MergeFrom(self.initial.to_proto())
        assert(shard.id == self.hash)
        return shard

    @classmethod
    def from_proto(cls, obj):
        Block.from_proto(obj.initial)

        return super(Shard, cls).from_proto(obj, cls(
            id=obj.id,
            uid=obj.uid,
            name=obj.name,
            desc=obj.desc,
            public=obj.public,
            meta=obj.meta,
            initial=obj.initial.id,
            active=False))

ShardProxy.initialize(Shard)
