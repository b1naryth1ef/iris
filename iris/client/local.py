import time, thread, logging

from ..data.base_pb2 import *
from ..common.util import generate_random_number
from ..db.user import User
from ..network.connection import Protocol, ProtocolUpdateEvent
from .remote import RemoteClient

log = logging.getLogger(__name__)

class LocalClient(object):
    def __init__(self, user, shards, port, seeds=None):
        self.user = user
        self.shards = shards
        self.port = port
        self.seeds = seeds

        self.server = Protocol()
        self.server.listen({'port': port})

        self.clients = {}

    def add_shard(self, id):
        packet = PacketRequestShards()
        packet.maxsize = 1
        packet.shards.append(id)
        packet.peers = True
        map(lambda i: i.send(packet), self.clients.values())

    def send_handshake(self, remote):
        packet = PacketBeginHandshake()
        packet.pubkey = str(self.user.public_key).encode('hex')
        packet.nickname = self.user.nickname
        packet.timestamp = int(time.time())
        packet.challenge = remote.auth_challenge = generate_random_number(8)
        remote.send(packet)

    def run(self):
        log.info("Starting LocalClient up...")
        thread.start_new_thread(self.network_loop, ())

        log.info("Attempting to seed from %s seeds", len(self.seeds))
        for conns in self.seeds:
            socket = self.server.connect(conns)
            if not socket:
                log.error("Failed to seed from %s", conns)
                continue
            client = self.clients[socket.fileno()] = RemoteClient(self, socket)
            self.send_handshake(client)

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

