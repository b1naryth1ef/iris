import logging

from datetime import datetime

from .base import *
from .shard import Shard
from .user import User

log = logging.getLogger(__name__)

class Entry(BaseModel):
    HASH_FIELDS = ["shard", "author", "payload", "created"]

    shard = ForeignKeyField(Shard)
    author = ForeignKeyField(User)
    payload = BlobField(null=True)
    created = DateTimeField(default=datetime.utcnow)

class EntryStamp(BaseModel):
    entry = ForeignKeyField(Entry, related_name='stamps')
    notary = ForeignKeyField(User)
    data = BlobField()
    

