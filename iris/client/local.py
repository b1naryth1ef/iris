import time, thread, logging, os, miniupnpc, socket, requests, json

from ..data.base_pb2 import *
from ..common.util import generate_random_number
from ..db.user import User
from ..db.shard import Shard
from ..network.connection import Protocol, ProtocolUpdateEvent
from .remote import RemoteClient
from .ticket import Ticket, TicketType

log = logging.getLogger(__name__)

class LocalClient(object):
    def __init__(self, user, shards, port, seeds=None, upnp=False):
        self.user = user
        self.port = port
        self.seeds = seeds
        self.shards = {i.id: i for i in shards}
        self.clients = {}
        self.tickets = {}

        self.ip = os.getenv("IRIS_IP") or requests.get("http://ipv4.icanhazip.com/").content.strip()

        # Maxiumum peers we will keep
        self.max_peers = 128

        # Attempt to map UPnP
        if upnp:
            thread.start_new_thread(self.update_upnp_loop, ())

        thread.start_new_thread(self.update_tickets_loop, ())

        self.server = Protocol()
        self.server.listen({'port': port})

    def get_local_ip(self):
        return [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]

    def update_tickets_loop(self):
        while True:
            for ticket in self.tickets.values():
                if ticket.is_expired():
                    self.on_ticket_expired(ticket)
                    del self.tickets[ticket.id]
            time.sleep(5)

    def update_upnp_loop(self):
        while True:
            self.map_upnp()
            time.sleep(300)

    def map_upnp(self):
        log.debug("Attempting to UPnP Hole Punch...")
        u = miniupnpc.UPnP()
        u.discoverdelay = 2000

        devcount = u.discover()
        if devcount > 1:
            return log.warning("Found more than 1 UPnP device, skipping")

        if devcount == 0:
            return log.warning("Found no UPnP devices, skipping")

        # Select the IGD
        u.selectigd()

        # Loop over existing port-maps
        for i in range(1024):
            mp = u.getgenericportmapping(i)

            if not mp:
                break

            if mp[3].startswith('IRIS.'):
                if m[2][0] == self.get_local_ip() and m[2][1] == self.port:
                    log.warning("Found previously UPnP mapped port, skipping")
                    return

        return u.addportmapping(self.port, 'TCP', self.get_local_ip(), self.port, "IRIS.", '')

    def on_ticket_expired(self, ticket):
        if ticket.type == TicketType.WARMUP:
            if not len(self.clients):
                raise Exception("Failed to seed from any clients in time!")
            log.debug("WARMUP ticket expired, but we have peers anyway")
        elif ticket.type == TicketType.JOIN_SHARD:
            log.warning("Failed to join shard %s, could not find it amongst peers!", ticket.shard_id)

    def on_ticket_triggered_pre(self, ticket, client, packet):
        if ticket not in self.tickets:
            return

        ticket = self.tickets[ticket]
        ticket.triggered(client, packet)

    def on_ticket_triggered_post(self, ticket, client, packet):
        if ticket not in self.tickets:
            return

        ticket = self.tickets[ticket]

        if ticket.type == TicketType.WARMUP:
            if len(ticket.triggers) == ticket.peers:
                log.debug("Warmup ticket completed, WOULD REQUEST UPDATES HERE")
                ticket.delete()
        elif ticket.type == TicketType.JOIN_SHARD:
            if not len(packet.shards):
                return
            shard = Shard.get(Shard.id == packet.shards[0].id)
            self.sync_shard(shard)
            ticket.delete()
        elif ticket.type == TicketType.SYNC_SHARD:
            if not len(packet.entries):
                return

            self.sync_entries(ticket.shard_id, packet.entries)
            ticket.delete()

    def add_ticket(self, ticket):
        ticket.parent = self
        self.tickets[ticket.id] = ticket
        return ticket

    def add_shard(self, id):
        try:
            shard = Shard.get(Shard.id == id)
            if not shard.active:
                log.info("Shard exists but is not active, reactivating and syncing")
                shard.active = True
                self.sync_shard(shard)
            return
        except Shard.DoesNotExist: pass

        ticket = self.add_ticket(Ticket(TicketType.JOIN_SHARD, shard_id=id))
        packet = PacketRequestShards()
        packet.limit = 1
        packet.shards.append(id)
        packet.peers = True
        map(lambda i: i.send(packet, ticket=ticket), self.clients.values())

        # TODO: subscribe

    def sync_shard(self, shard):
        ticket = self.add_ticket(Ticket(TicketType.SYNC_SHARD, shard_id=shard.id))
        packet = PacketSearchEntries()
        packet.shard = shard.id
        packet.query = json.dumps({})
        packet.limit = 1024

        # TODO: only send to ones we know have the shard
        map(lambda i: i.send(packet, ticket=ticket), self.clients.values())

    def sync_entries(self, shard, entries):
        ticket = self.add_ticket(Ticket(TicketType.SYNC_ENTRIES, entries=entries))
        packet = PacketRequestEntries()
        packet.shard = shard
        packet.entries.extend(entries)
        packet.limit = 1024
        packet.with_authors = True
        packet.with_stamps = True
        
        # TODO: get peers, divide entry set, create seperate tickets, skip existing entries
        map(lambda i: i.send(packet, ticket=ticket), self.clients.values())

    def send_handshake(self, remote, ticket=None):
        packet = PacketBeginHandshake()
        packet.peer.ip = self.ip
        packet.peer.port = self.port
        packet.peer.user.CopyFrom(self.user.to_proto())
        packet.timestamp = int(time.time())
        packet.challenge = remote.auth_challenge = generate_random_number(8)
        remote.send(packet, ticket=ticket)

    def add_peer(self, conn, ticket=None):
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
        self.send_handshake(client,ticket)
        return True

    def run(self):
        log.info("Starting LocalClient up...")
        thread.start_new_thread(self.network_loop, ())

        log.info("Attempting to seed from %s seeds", len(self.seeds))
        ticket = self.add_ticket(Ticket(TicketType.WARMUP, peers=len(self.seeds), duration=15))
        map(lambda i: self.add_peer(i, ticket), self.seeds)

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

