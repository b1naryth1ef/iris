import logging

from .base import *
from .shard import Shard

log = logging.getLogger(__name__)

class Peer(BaseModel):
    id = IntegerField(primary_key=True)

    ip = CharField(max_length=15)
    port = IntegerField()

class PeerShardSubscription(BaseModel):
    id = IntegerField(primary_key=True)

    peer = ForeignKeyField(Peer)
    shard = ForeignKeyField(Shard)

    active = BooleanField(default=True)

