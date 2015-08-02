import logging

from datetime import datetime

from ..common.identity import IdentityMixin

from .base import *

log = logging.getLogger(__name__)

class User(BaseModel, IdentityMixin):
    HASH_FIELDS = ['id', 'public_key', 'nickname']

    public_key = BlobField()

    # User nickname. This doesn't need to be unique.
    nickname = CharField(max_length=128, null=True)

    # If true, we will never interact with this user
    blocked = BooleanField(default=False)

    # When did we first and last see them
    first_authed = DateTimeField(default=datetime.utcnow)
    last_authed = DateTimeField(default=datetime.utcnow)

