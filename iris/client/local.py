import os, time, threading, json, socket, logging
# import miniupnpc, requests

import logging, miniupnpc, requests

from ..data.base_pb2 import *
from ..common.util import generate_random_number
from ..db.user import User
from ..db.shard import Shard
from ..network.connection import Protocol, ProtocolUpdateEvent
from .remote import RemoteClient
from .ticket import Ticket, TicketType
from .chain import Chain

log = logging.getLogger(__name__)

class LocalClient(object):
    """
    Represents "our" client, e.g. the client we are currently running. Serves
    as the parent object for almost every other connection/object we handle.
    """
    def __init__(self, user, shards, config, seeds=None):
        self.user = user
        self.shards = {}
        self.config = config
        self.seeds = seeds

        # Add shards
        for shard in shards:
            self.add_shard(shard, subscribe=False)

        # List of peers we are connected too
        self.clients = {}
        self.tickets = {}

        # Threads
        self.thread_upnp = threading.Thread(target=self.update_upnp_loop)
        self.thread_tickets = threading.Thread(target=self.update_tickets_loop)
        self.thread_network = threading.Thread(target=self.network_loop)

    def send_to_shard(self, shard, packet, ticket=None):
        """
        Sends a packet to all peers that are part of a shard
        """
        for client in self.clients.values():
            if shard.id in client.shards:
                client.send(packet, ticket=ticket)

    def run(self):
        # If we're going to be peering, create a server and listen on it
        if self.config.local.enabled:
            log.info("Local peer server enabled, setting up and listening")
            self.server = Protocol()
            port = self.config.local.port or 0
            self.port = self.server.listen({'port': port, 'host': self.config.local.host})

        # Attempt to grab this machines IPv4 IP
        try:
            self.ip = os.getenv("IRIS_IP") or requests.get("http://ipv4.icanhazip.com/").content.strip()
        except requests.exceptions.ConnectionError:
            log.warning("Could not resolve remote (e.g. NAT) IP, using LAN IP")
            # TOOD: thats not a local ip...
            self.ip = "127.0.0.1"

        # Attempt to map UPnP
        if self.config.nat.upnp:
            self.thread_upnp.start()

        # Start the update tickets thread
        self.thread_tickets.start()

        log.info("Starting LocalClient up...")
        self.thread_network.start()

        log.info("Attempting to seed from %s seeds", len(self.seeds))
        ticket = self.add_ticket(Ticket(TicketType.WARMUP, peers=len(self.seeds), duration=15))
        list(map(lambda i: self.add_peer(i, ticket), self.seeds))

    def get_local_ip(self):
        return [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]

    def update_tickets_loop(self):
        return
        while True:
            for ticket in self.tickets.values():
                if ticket.is_expired():
                    self.on_ticket_expired(ticket)
                    ticket.delete()
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

    def on_ticket_error(self, ticket, err):
        ticket = self.tickets.get(ticket)
        if ticket:
            ticket.delete(err)

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
                ticket.complete()
        elif ticket.type == TicketType.JOIN_SHARD:
            if not len(packet.shards):
                return

            log.info("Completed JOIN_SHARD request")
            shard = Shard.get(Shard.id == packet.shards[0].id)
            self.sync_shard(shard)
            ticket.complete(shard)
        elif ticket.type == TicketType.SYNC_SHARD:
            if len(ticket.triggers) == ticket.peers:
                ticket.complete()

    def add_ticket(self, ticket):
        ticket.parent = self
        self.tickets[ticket.id] = ticket
        return ticket

    def add_shard(self, id, subscribe=True, timeout=30):
        """
        Add a shard and optionally subscribe to it. If we don't have this shard
        stored locally, we'll attempt to sync it from the network.
        """
        try:
            shard = Shard.get(Shard.id == id)
        except Shard.DoesNotExist:
            # We don't have this shard locally, so lets request it from the network
            ticket = self.add_ticket(Ticket(TicketType.JOIN_SHARD, shard_id=id, timeout=timeout))
            packet = PacketRequestShards()
            packet.shards.append(id)
            packet.peers = True

            # Send it to all peers we have, regardless of whether they announce this
            for client in self.clients.values():
                client.send(packet, ticket=ticket)

            # Wait for the ticket to complete
            shard = ticket.wait()

        # Make sure we start the mining process
        if shard.id not in self.shards or subscribe:
            shard.active = True
            self.shards[shard.id] = shard
            self.shards[shard.id].chain = Chain(shard)
            self.shards[shard.id].chain.start_miner(self.user)

        # Optionally, subscribe to it
        if subscribe:
            packet = PacketSubscribeShard()
            packet.shard = shard.id
            packet.state = True
            self.send_to_shard(shard, packet)

        return shard

    def sync_shard(self, shard):
        # Get the count of peers for the shard we want to sync
        peers = len([0 for c in self.clients.values() if shard.id in c.shards])

        # Generally we don't want to sync with less than 3 peers
        if peers < 3:
            log.warning("Performing an UNSAFE sync on a network with less than 3 peers")

        ticket = self.add_ticket(Ticket(TicketType.SYNC_SHARD, shard_id=shard.id, peers=peers))
        packet = PacketRequestBlocks()
        packet.shard = shard.id
        packet.brief = False
        packet.start_index = -1
        packet.stop_index = -128
        self.send_to_shard(shard, packet, ticket)

        return ticket

    def send_handshake(self, remote, ticket=None):
        packet = PacketBeginHandshake()
        packet.peer.ip = self.ip
        packet.peer.port = self.port
        packet.peer.user.CopyFrom(self.user.to_proto())
        packet.timestamp = int(time.time())
        packet.challenge = remote.auth_challenge = generate_random_number(8)
        packet.shards.extend(self.shards.keys())
        remote.send(packet, ticket=ticket)

    def add_peer(self, conn, ticket=None):
        if len(self.clients) >= self.config.max_peers:
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

    def network_loop(self):
        log.info("Network loop has started")
        for update in self.server.poll():
            if update.type == ProtocolUpdateEvent.NEW:
                if len(self.clients) >= self.config.max_peers:
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

