import time

from ..common.util import random_uuid

class TicketType(object):
    WARMUP = 1
    JOIN_SHARD = 2
    SYNC_SHARD = 3
    SYNC_ENTRIES = 4

class Ticket(object):
    def __init__(self, ttype, duration=None, **kwargs):
        self.id = random_uuid()
        self.type = ttype
        self.duration = duration or 120
        self.start = time.time()
        self.triggers = []

        self.__dict__.update(kwargs)

    def delete(self):
        del self.parent.tickets[self.id]

    def is_expired(self):
        return (self.start + self.duration) < time.time()

    def triggered(self, client, packet):
        self.triggers.append((client, packet))

