import logging
from collections import OrderedDict

from ..common.identity import IdentityMixin
from .base import *

log = logging.getLogger(__name__)

class Shard(BaseModel):
    """
    Shards represent a divided section of the network that segments data,
    allowing overlying clients to provide a type of "board" or "sub-site"
    breakout. All other type of data apart from users is hierarcherly organized
    under a shard.
    """
    name = CharField(max_length=128)
    desc = CharField(max_length=2048)
    public = BooleanField(default=True)
    meta = BlobField()

