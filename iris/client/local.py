import time, thread, logging, stun, os

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
        
        # We get STUN info so we can allow others to connect to us via IP
        self.ip = os.getenv("IRIS_IP") or stun.get_ip_info(stun_host='stun.ekiga.net')[1]
        
        # Maxiumum peers we will keep
        self.max_peers = 128

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
        packet.peer.ip = self.ip
        packet.peer.port = self.port 
        packet.peer.user.CopyFrom(self.user.to_proto())
        packet.timestamp = int(time.time())
        packet.challenge = remote.auth_challenge = generate_random_number(8)
        remote.send(packet)

    def add_peer(self, conn):
        if len(self.clients) >= self.max_peers:
            log.warning("Skipping adding peer `%s`, we have our max number of peers (%s)",
                conn, len(self.clients))
            return

        log.info("Attempting to add peer at %s", conn)
        socket = self.server.connect(conn)
        if not socket:
            log.error("Failed to add peer: `%s`", conn)
            return False
        client = self.clients[socket.fileno()] = RemoteClient(self, socket)
        self.send_handshake(client)
        return True

    def run(self):
        log.info("Starting LocalClient up...")
        thread.start_new_thread(self.network_loop, ())

        log.info("Attempting to seed from %s seeds", len(self.seeds))
        map(self.add_peer, self.seeds)

    def network_loop(self):
        for update in self.server.poll():
            if update.type == ProtocolUpdateEvent.NEW:
                if len(self.clients) >= self.max_peers:
                    log.warning("Denying connection from, we have our max number of peers (%s)",
                        len(self.clients))
                    update.socket.close()
                    continue
                client = self.clients[update.socket.fileno()] = RemoteClient(self, update.socket)
                client.wait_for_handshake()

            if update.type == ProtocolUpdateEvent.DATA:
                client = self.clients[update.socket]
                client.update()

            if update.type == ProtocolUpdateEvent.CLOSE:
                del self.clients[update.socket]

    def stop(self):
        self.server.close()

