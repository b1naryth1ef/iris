import time

from ..data.base_pb2 import *
from ..common.util import random_uuid

from .base import *
from .user import User
from .entry import Entry

class Block(BaseModel, SignatureModel('solver')):
    HASH_FIELDS = ['uid', 'parent', 'solver', 'time', 'position', 'initial', 'entries']

    uid = CharField(max_length=32, default=random_uuid)
    parent = ForeignKeyField('self', null=True)
    solver = ForeignKeyField(User)
    time = IntegerField(default=lambda: int(time.time()))

    # The position of this block, as text so we can go forever!
    position = TextField()

    # True if this is the first block in a chain.
    initial = BooleanField(default=False)

    # Utility only, blocks are never bound to a single shard
    shard_id = CharField(max_length=64, null=True)

    # Proof of work "salt"
    proof = IntegerField()
    commited = BooleanField(default=False)

    @property
    def entries(self):
        return list(map(lambda i: i.entry.id,
            BlockEntry.select(BlockEntry.entry).where(BlockEntry.block == self)))

    @property
    def shard(self):
        from .shard import Shard
        return Shard.get(Shard.id == self.shard)

    @classmethod
    def from_proto(cls, obj):
        for entry in obj.entries:
            BlockEntry.get_or_create(
                block=obj.id,
                entry=entry.id)

        for entry in obj.ientries:
            Entry.from_proto(entry)

        User.from_proto(obj.solver)

        super().from_proto(obj, cls(
            id=obj.id,
            uid=obj.uid,
            parent=None if obj.initial else obj.parent,
            solver=obj.solver.id,
            time=obj.time,
            position=obj.position,
            initial=obj.initial,
            proof=obj.proof,
            signature=obj.signature))

    def to_proto(self, with_entries=False):
        block = IBlock()
        block.id = self.id
        block.uid = self.uid
        if self.parent:
            block.parent.MergeFrom(self.parent.to_proto())
        block.solver.MergeFrom(self.solver.to_proto())
        block.time = self.time
        block.position = self.position
        block.initial = self.initial
        block.proof = self.proof
        block.signature = self.signature
        block.entries.extend(self.entries)

        if with_entries:
            block.ientries.extend(list(map(lambda i: i.to_proto(),
                Entry.select().where((Entry.id << self.entries)))))

        assert(block.id == self.hash)
        return block

class BlockEntry(BaseModel):
    id = IntegerField(primary_key=True)
    block = ForeignKeyField(Block)
    entry = ForeignKeyField(Entry)

