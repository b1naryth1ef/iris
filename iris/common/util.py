import random
from data.base_pb2 import *

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

