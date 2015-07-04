import time, thread

from client.remote import RemoteClient
from network.connection import Protocol, ProtocolUpdateEvent

"""
udp = UDPProtocol(9090)
udp.listen()

for update in udp.poll():
    # If we're a new connection
    if update.type == Updates.NEW_CONNECTION:
        self.add_connection(Connection(update.socket))

    if update.type == Updates.NEW_MESSAGE:
        conn = self.get_connection(update.socket)
        conn.read()

    if update.type == Updates.CLOSE_CONNECTION:
        conn = self.get_connection(update.socket)
        conn.close()
"""

class LocalClient(object):
    def __init__(self, port, seeds=None):
        self.port = port
        self.seeds = seeds

        self.server = Protocol()
        self.server.listen({'port': port})

        self.clients = {}

    def run(self):
        thread.start_new_thread(self.network_loop, ())

        for conns in self.seeds:
            socket = self.server.connect(conns)
            if not socket:
                print 'failed to seed from %s' % conns
                continue
            client = self.clients[socket.fileno()] = RemoteClient(self, socket)
            client.handshake()

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

