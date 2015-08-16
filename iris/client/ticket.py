import time, threading, logging

from ..common.async import Future
from ..common.util import random_uuid

log = logging.getLogger(__name__)

class TicketType(object):
    WARMUP = 1
    JOIN_SHARD = 2
    SYNC_SHARD = 3
    SYNC_ENTRIES = 4

class TicketExpired(Exception):
    pass

class Ticket(object):
    def __init__(self, ttype, timeout=None, **kwargs):
        self.id = random_uuid()
        self.type = ttype
        self.timeout = timeout or 120
        self.start = time.time()
        self.triggers = []
        self.future = Future()

        self.__dict__.update(kwargs)

        threading.Thread(target=self._expire).start()

    def _expire(self):
        self.future.wait(self.timeout)
        log.info("Ticket {} ({}) has completed/expired ({})".format(self.id, self.type, self.future.completed))

        if not self.future.completed:
            self.parent.on_ticket_expired(self)

        self.delete(TicketExpired())

    def delete(self, exe=None):
        del self.parent.tickets[self.id]

        if not self.future.completed:
            self.future.cancel(exe)

    def triggered(self, client, packet):
        self.triggers.append((client, packet))

    def complete(self, value=None):
        if not self.future.completed:
            self.future.done(value)

    def wait(self, *args, **kwargs):
        return self.future.wait(*args, **kwargs)

