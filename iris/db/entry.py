import logging, json, arrow

from datetime import datetime

from ..data.base_pb2 import *
from ..common.errors import *

from .base import *
from .shard import Shard
from .user import User

log = logging.getLogger(__name__)

class Entry(BaseModel, SignatureModel('author')):
    HASH_FIELDS = ["shard", "author", "payload", "created"]

    shard = ForeignKeyField(Shard)
    author = ForeignKeyField(User)
    payload = BlobField()
    created = DateTimeField(default=datetime.utcnow)
    proof = IntegerField()

    def to_proto(self, with_authors=False, with_stamps=False):
        entry = IEntry()
        entry.id = self.id
        entry.shard = self.shard.id
        entry.author = self.author.id
        entry.payload = str(self.payload)
        entry.signature = str(self.signature)
        entry.created = self.created.isoformat()
        entry.proof = self.proof

        if with_stamps:
            entry.stamps.extend(map(lambda i: i.to_proto, self.stamps))

        if with_authors:
            entry.author_obj.CopyFrom(self.author.to_proto())

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
            payload=obj.payload,
            proof = self.proof,
            signature=obj.signature,
            created=arrow.get(obj.created).datetime.replace(tzinfo=None))

        if not new.validate_proof():
            raise TrustException("Invalid proof of work", TrustException.Level.MALICIOUS)

        super(Entry, cls).from_proto(obj, new)

    @classmethod
    def create_from_json(cls, author, obj, proof=True):
        self = cls()
        self.shard = Shard.get(Shard.id == obj['shard'])
        self.author = author
        self.payload = json.dumps(obj['payload'])
        self.id = self.hash

        # Calculate proof for hash
        if proof:
            worker = self.shard.get_pow(
            self.proof = worker.work(self.hash)

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

