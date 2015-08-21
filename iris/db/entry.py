import logging, json, arrow

from datetime import datetime

from ..data.base_pb2 import *
from ..common.errors import *
from ..common.util import encode_sha256

from .base import *
from .user import User
from .proxies import ShardProxy

log = logging.getLogger(__name__)


class Entry(BaseModel, SignatureModel('author')):
    HASH_FIELDS = ["shard", "author", "meta", "payload_hash", "created"]

    shard = ForeignKeyField(ShardProxy)
    author = ForeignKeyField(User)
    meta = BlobField()
    payload_hash = CharField(max_length=64)
    created = DateTimeField(default=datetime.utcnow)
    proof = IntegerField()

    # Payload doesn't have to be synced
    payload = BlobField(null=True)

    def set_payload(self, payload):
        self.payload = payload
        self.payload_hash = encode_sha256(payload.encode('utf-8'))

    @property
    def block(self):
        from .block import BlockEntry
        try:
            return BlockEntry.get(BlockEntry.entry == self).block
        except BlockEntry.DoesNotExist:
            return None

    @property
    def commited(self):
        return self.block and self.block.commited

    @classmethod
    def get_uncommited_entries(cls, shard):
        return cls.select().where(
            (cls.block == None) &
            (cls.shard == shard))

    def to_proto(self, with_authors=False, with_stamps=False, with_payload=False):
        entry = IEntry()
        entry.id = self.id
        entry.shard = self.shard.id
        entry.author = self.author.id
        entry.meta = str(self.meta)
        entry.payload_hash = str(self.payload_hash)
        entry.signature = str(self.signature)
        entry.created = self.created.isoformat()
        entry.proof = self.proof

        if with_stamps:
            entry.stamps.extend(map(lambda i: i.to_proto, self.stamps))

        if with_authors:
            entry.author_obj.CopyFrom(self.author.to_proto())

        if with_payload:
            entry.payload = self.payload

        assert(entry.id == self.hash)
        return entry

    def validate_proof(self):
        worker = self.shard.get_pow()
        return worker.validate(self.hash, self.proof)

    @classmethod
    def from_proto(cls, obj):
        new = cls(
            id=obj.id,
            shard=obj.shard,
            author=obj.author,
            meta=obj.meta,
            payload_hash=obj.payload_hash,
            payload=obj.payload,
            proof = obj.proof,
            signature=obj.signature,
            created=arrow.get(obj.created).datetime.replace(tzinfo=None))

        # TODO: check hash of payload

        if not new.validate_proof():
            raise TrustException("Invalid proof of work", TrustException.Level.MALICIOUS)

        super(Entry, cls).from_proto(obj, new)

    @classmethod
    def create_from_json(cls, author, obj, proof=True):
        raise Exception("DEPRECATED")
        self = cls()
        self.shard = Shard.get(Shard.id == obj['shard'])
        self.author = author
        self.payload = json.dumps(obj['payload'])
        self.id = self.hash

        # Calculate proof for hash
        if proof:
            worker = self.shard.get_pow()
            self.proof, _ = worker.work(self.hash)

        self.save(force_insert=True)
        return self

class EntryStamp(BaseModel, SignatureModel('notary')):
    HASH_FIELDS = ['entry', 'notary', 'parent', 'created']

    entry = ForeignKeyField(Entry, related_name='stamps')
    notary = ForeignKeyField(User)
    parent = ForeignKeyField('self', related_name='children', null=True)
    created = DateTimeField(default=datetime.utcnow)

    @classmethod
    def from_proto(cls, obj):
        return super(EntryStamp, cls).from_proto(obj, cls(
            id=obj.id,
            entry=obj.entry,
            notary=obj.notary,
            parent=obj.parent,
            created=arrow.get(obj.created).datetime.replace(tzinfo=None),
            signature=obj.signature))

    def to_proto(self):
        stamp = IStamp()
        stamp.id = self.id
        stamp.entry = self.entry.id
        stamp.notary = self.notary.id
        stamp.parent = self.parent.id or ''
        stamp.created = self.created.isoformat()
        stamp.signature = str(self.signature)
        return stamp

