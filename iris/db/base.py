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
                value = str(value).encode('hex')

            obj[field] = value
        
        return to_ordered(obj)

    def get_hash_dict(self):
        obj = self.to_dict(getattr(self, 'HASH_FIELDS', None), False)
        if 'id' in obj:
            del obj['id']
        return IrisJSONEncoder().encode(obj)

    @property
    def hash(self):
        return encode_sha256(self.get_hash_dict())

    @classmethod
    def from_proto(cls, obj, result):
        # If the sender lied about the ID, they are trying to be malicious
        if result.id != result.hash:
            raise TrustException("Recieved serialized version of %s, with an invalid or spoofed hash (%s vs %s)" %
                (cls.__name__, result.id, result.hash), TrustException.Level.MALICIOUS)

        try:
            # Grab an existing version
            obj = cls.get(cls.id == obj.id)

            # If our hashes don't match, one of us have invalid data
            if obj.hash != result.hash:
                raise TrustException("Found existing version of %s, but our hashes do not match (%s vs %s)" %
                    (cls.__name__, obj.hash, result.hash), TrustException.Level.INACCURATE)
            return obj
        except cls.DoesNotExist:
            result.save(force_insert=True)
            return result

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
