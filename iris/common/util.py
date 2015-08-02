import random, uuid, json, hashlib, datetime

from collections import OrderedDict
from ..data.base_pb2 import *

class IrisJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            return super(DateTimeJSONEncoder, self).default(obj)

def to_ordered(obj):
    return OrderedDict(sorted(obj.items()))

def encode_sha256(s):
    m = hashlib.sha256()
    m.update(s)
    return m.hexdigest()

def ordered_from_json(s):
    return json.JSONDecoder(object_pairs_hook=OrderedDict).decode(s)

def random_uuid():
    return str(uuid.uuid4()).replace('-', '')

def generate_random_number(dig):
    return int(reduce(lambda a, b: a + b, map(lambda _: str(random.randint(0, 9)), range(dig))))

def packet_from_id(id):
    name = 'Packet' + PacketType.keys()[PacketType.values().index(id)]
    return globals()[name]

def packet_to_id(obj):
    name = obj.__class__.__name__.split('t', 1)[1]

    if name not in PacketType.keys():
        raise Exception("Unknown packet type: {}".format(name))

    return dict(PacketType.items())[name]

