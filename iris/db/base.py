import os, logging, sys, peewee

from collections import OrderedDict
from peewee import *

from ..common.util import ordered_from_json, encode_sha256, to_ordered, IrisJSONEncoder

log = logging.getLogger(__name__)
db = SqliteDatabase(None)

__all__ = ['BaseModel', 'init_db', 'db'] + peewee.__all__

class BaseModel(Model):
    class Meta:
        database = db

    # ID's are equal to sha256(json(ordered_content))
    id = CharField(unique=True, primary_key=True, max_length=64)

    def to_dict(self, fields=None, resolve=True):
        obj = {}
        for field in (fields or self._meta.get_field_names()):
            value = getattr(self, field)

            if hasattr(value, '__class__') and issubclass(value.__class__, BaseModel):
                if resolve:
                    value = value.to_dict(resolve=True)
                else:
                    value = getattr(value, value.__class__._meta.get_primary_key_fields()[0].name)

            if field.endswith('_key'):
                value = value.encode('hex')

            obj[field] = value
        
        return to_ordered(obj)

    @property
    def hash(self):
        obj = self.to_dict(getattr(self, 'HASH_FIELDS'), False)
        del obj['id']
        return encode_sha256(IrisJSONEncoder().encode(obj))

def create_db(path):
    if os.path.exists(path):
        raise Exception("Database at path `{}` already exists".format(path))

    db.init(path)

    from shard import Shard
    from user import User
    from entry import Entry, EntryStamp
    from seed import Seed

    db.create_tables([Shard, User, Entry, EntryStamp, Seed])

def init_db(path):
    db.init(path)
