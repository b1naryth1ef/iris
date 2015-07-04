import time, thread, logging

from client.remote import RemoteClient
from network.connection import Protocol, ProtocolUpdateEvent

log = logging.getLogger(__name__)

class LocalClient(object):
    def __init__(self, identity, port, seeds=None):
        self.identity = identity
        self.port = port
        self.seeds = seeds

        self.server = Protocol()
        self.server.listen({'port': port})

        self.clients = {}

    def run(self):
        log.info("Starting LocalClient up...")
        thread.start_new_thread(self.network_loop, ())

        log.info("Attempting to seed mesh from %s seeds", len(self.seeds))
        for conns in self.seeds:
            socket = self.server.connect(conns)
            if not socket:
                log.error("Failed to seed from %s", conns)
                continue
            client = self.clients[socket.fileno()] = RemoteClient(self, socket)
            client.send_handshake()

        while True:
            time.sleep(1)

    def network_loop(self):
        for update in self.server.poll():
            if update.type == ProtocolUpdateEvent.NEW:
                client = self.clients[update.socket.fileno()] = RemoteClient(self, update.socket)
                client.wait_for_handshake()

            if update.type == ProtocolUpdateEvent.DATA:
                client = self.clients[update.socket]
                client.update()

            if update.type == ProtocolUpdateEvent.CLOSE:
                del self.clients[update.socket]

    def stop(self):
        self.server.close()

