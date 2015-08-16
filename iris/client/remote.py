import time, threading, logging, json, datetime

from ..data.base_pb2 import *
from ..common.util import packet_from_id, packet_to_id, generate_random_number
from ..db.user import User
from ..db.shard import Shard
from ..db.entry import Entry, EntryStamp

from .packet import PacketWrapper

log = logging.getLogger(__name__)

class RemoteClient(object):
    def __init__(self, parent, socket):
        self.parent = parent
        self.socket = socket

        self.conn = None
        self.user = None
        self.auth_completed = False
        self.auth_challenge = None

        # List of shards this remote client is subscribed too
        self.shards = set()

    def modify_shard_subscription(self, shard, state):
        # Grab or create the subscription (kind of weird we create on unsub...)
        sub, created = UserSub.get_or_create(
            user=self.user,
            shard=shard)

        # If we're subscribing, lets note it down
        if state:
            sub.active = True
            self.shards.add(shard.id)
        else:
            sub.active = False

            if shard.id in self.shards:
                self.shards.remove(shard.id)

        sub.save()

    def wait_for_handshake(self, delay=5):
        def _f():
            time.sleep(delay)
            if not self.auth_completed or not self.user:
                self.close("failed to authenticate in time")
        threading.Thread(target=_f).start()

    def update(self):
        inner, outer = self.recv()
        if not inner or not outer:
            return

        packet = PacketWrapper(self, inner, outer)

        if outer.ticket:
            self.parent.on_ticket_triggered_pre(outer.ticket, self, packet)

        try:
            self.handle(packet)
        except Exception as e:
            log.exception("Error handling packet:")
            if outer.ticket:
                self.parent.on_ticket_error(outer.ticket, e)
            return

        if outer.ticket:
            self.parent.on_ticket_triggered_post(outer.ticket, self, packet)

    @property
    def fileno(self):
        return self.socket.fileno()

    def send(self, packet, ticket=None, encrypt=True, to=None):
        encrypt = encrypt and self.user
        data = packet.SerializeToString()

        if encrypt:
            data = self.parent.user.encrypt(data, self.user)

        obj = Packet()
        obj.type = packet_to_id(packet)
        obj.data = data

        if ticket:
            if isinstance(ticket, str):
                obj.ticket = ticket
            else:
                obj.ticket = ticket.id

        log.debug("Sending packet %s to remote %s (%s)",
                packet.__class__.__name__, self.user, 'encrypted' if encrypt else '')
        self.socket.send(obj.SerializeToString())

    def recv(self):
        data = self.socket.recv(4096)

        if not data:
            log.info("Lost connection to remote client %s", self.user)
            self.close()
            return None, None

        outer = Packet()
        outer.ParseFromString(data)

        if outer.type == 0:
            raise Exception("Invalid packet data read: `{}`".format(data))

        data = outer.data

        if self.user and self.auth_completed:
            data = self.parent.user.decrypt(data, self.user)

        packet = packet_from_id(outer.type)()
        packet.ParseFromString(data)

        return packet, outer

    def close(self, reason=None):
        log.warning("Disconnecting remote client %s (%s)", self.user, reason or 'no reason')
        if reason:
            obj = PacketClose()
            obj.reason = reason
            self.send(obj)
        self.socket.close()

    def handle(self, packet):
        log.debug("Recieved packet %s", packet.inner.__class__.__name__)

        if isinstance(packet.inner, PacketBeginHandshake):
            return self.handle_begin_handshake(packet)
        elif isinstance(packet.inner, PacketDenyHandshake):
            return self.handle_deny_handshake(packet)
        elif isinstance(packet.inner, PacketAcceptHandshake):
            return self.handle_accept_handshake(packet)
        elif isinstance(packet.inner, PacketCompleteHandshake):
            return self.handle_complete_handshake(packet)

        if self.user and self.auth_completed:
            if isinstance(packet.inner, PacketRequestPeers):
                return self.handle_request_peers(packet)
            elif isinstance(packet.inner, PacketRequestShards):
                return self.handle_request_shards(packet)
            elif isinstance(packet.inner, PacketListPeers):
                return self.handle_list_peers(packet)
            elif isinstance(packet.inner, PacketListShards):
                return self.handle_list_shards(packet)
            elif isinstance(packet.inner, PacketSubscribeShard):
                return self.handle_subscribe_shard(packet)
            elif isinstance(packet.inner, PacketOfferblock):
                return self.handle_offer_block(packet)
            elif isinstance(packet.inner, PacketRequestBlocks):
                return self.handle_request_blocks(packet)
            elif isinstance(packet.inner, PacketListBlocks):
                return self.handle_list_blocks(packet)

        log.warning("Failed to handle packet %s", packet.inner.__class__.__name__)

    def handle_begin_handshake(self, packet):
        # We do not allow re-negoationing or a new handshake
        if self.user:
            self.close("R001 invalid handshake packet")
            raise Exception("R001: remote client sent handshake packet after a handshake was completed")

        diff = (time.time() - packet.timestamp)
        if abs(diff) > 30:
            self.close("R002: timestamp is too skewed to complete handshake")
            raise Exception("R002: timestamp skew to great")

        self.user = User.from_proto(packet.peer.user)
        self.conn = (packet.peer.ip, packet.peer.port)

        # Let's save this connection, in case we want to say hi later :)
        self.user.add_connection(self.conn)

        # Mark all the shards we have in common as subscribed
        shards = Shard.select().where(
            (Shard.id << tuple(packet.shards)) &
            (Shard.active == True))

        for shard in shards:
            self.modify_shard_subscription(shard, True)

        # Construct response
        resp = PacketAcceptHandshake()
        resp.peer.ip = self.parent.ip
        resp.peer.port = self.parent.port
        resp.peer.user.CopyFrom(self.parent.user.to_proto())
        resp.response = self.parent.user.encrypt(str(packet.challenge), self.user)
        resp.challenge = self.auth_challenge = generate_random_number(9)
        packet.respond(resp, encrypt=False)

    def handle_deny_handshake(self, packet):
        pass
        # TODO: this

    def handle_accept_handshake(self, packet):
        # If we are already authed, or didn't send this packet we're in trouble
        if not self.auth_challenge or self.user:
            self.close("R001 invalid handshake packet")
            raise Exception("R001: unexpected PacketAcceptHandshake packet")

        self.user = User.from_proto(packet.peer.user)
        self.conn = (packet.peer.ip, packet.peer.port)

        # Validate encoded stuff
        decoded = self.parent.user.decrypt(packet.response, self.user).decode('utf-8')
        if decoded != str(self.auth_challenge):
            self.close("invalid challenge response")
            raise Exception("Invalid challenge response for handshake accept ({} vs {})".format(
                decoded, self.auth_challenge
            ))

        self.auth_completed = True

        # Now lets complete the three-way-shake
        resp = PacketCompleteHandshake()
        resp.response = self.parent.user.encrypt(str(packet.challenge), self.user)
        packet.respond(resp, encrypt=False)

        # Finally request a list of peers
        self.send(PacketRequestPeers(maxsize=128, shards=self.parent.shards))

    def handle_complete_handshake(self, packet):
        if not self.auth_challenge or not self.user or self.auth_completed:
            self.close("R001 invalid handshake packet")
            raise Exception("R001: unexpected PacketCompleteHandshake packet")

        decoded = self.parent.user.decrypt(packet.response, self.user).decode('utf-8')
        if decoded != str(self.auth_challenge):
            self.close("invalid challenge response")
            raise Exception("Invalid challenge response for handshake completion")

        self.auth_completed = True
        log.info("Completed 3-way handshake with %s", self.user)

    def handle_request_peers(self, packet):
        peers = list(map(lambda i: i.conn, filter(lambda i: i != self and i and i.conn, self.parent.clients.values())))
        peers = peers[:packet.maxsize]

        log.info("Sending %s peers to %s", len(peers), self.user)
        resp = PacketListPeers()

        for client in self.parent.clients.values():
            # Never send ourself
            if client == self:
                continue

            rpeer = IPeer()
            rpeer.ip, rpeer.port = client.conn
            rpeer.user.CopyFrom(client.user.to_proto())
            resp.peers.extend([rpeer])

        packet.respond(resp)

    def handle_request_shards(self, packet):
        # TODO: send an error if we don't know about a shard
        if len(packet.shards):
            matched = [i for i in packet.shards if i in self.parent.shards]
            resp = PacketListShards()

            for shard in matched:
                shard = Shard.get(Shard.id == shard).to_proto()
                resp.shards.extend([shard])

            packet.respond(resp)

    def handle_list_peers(self, packet):
        log.info("Checking to see if we can peer with any of %s shared peers", len(packet.peers))

        peered = 0
        for rpeer in packet.peers:
            for lpeer in self.parent.clients.values():
                # If we have that user already, don't add
                if lpeer.user and lpeer.user.id == rpeer.user.id:
                    break
            else:
                peered += 1
                self.parent.add_peer('{}:{}'.format(rpeer.ip, rpeer.port))

        log.debug("Attempted to add %s peers from a shared peer set", peered)

    def handle_list_shards(self, packet):
        log.info("Processing a list of shards (%s)", packet.shards)
        for shard in packet.shards:
            if not Shard.select().where(Shard.id == shard.id).count():
                log.debug("Adding shard %s", shard.id)
                Shard.from_proto(shard)

        map(self.parent.add_peer, map(lambda i: '{}:{}'.format(i.ip, i.port), packet.peers))

    def handle_subscribe_shard(self, packet):
        # If we don't have the shard, we really can't do much with it
        try:
            shard = Shard.get(Shard.id == packet.shard)
        except Shard.DoesNotExist:
            log.info("Ignoring shard subscribe request (don't have shard)")
            return

        self.modify_shard_subscription(shard, packet.state)

    def handle_offer_block(self, packet):
        pass

    def handle_request_blocks(self, packet):
        pass

    def handle_list_blocks(self, packet):
        pass


