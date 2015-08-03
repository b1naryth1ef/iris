import logging, json

from datetime import datetime

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

    @classmethod
    def create_from_json(cls, author, obj):
        self = cls()
        self.shard = Shard.get(Shard.id == obj['shard'])
        self.author = author

        self.payload = json.dumps(obj['payload'])

        self.id = self.hash
        self.save(force_insert=True)

class EntryStamp(BaseModel, SignatureModel('notary')):
    HASH_FIELDS = ['entry', 'notary', 'parent', 'created']

    entry = ForeignKeyField(Entry, related_name='stamps')
    notary = ForeignKeyField(User)
    parent = ForeignKeyField('self', related_name='children')
    created = DateTimeField(default=datetime.utcnow)

    signature = BlobField()
    

