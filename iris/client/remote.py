import time, threading, logging, json, datetime

from ..data.base_pb2 import *
from ..common.util import packet_from_id, packet_to_id, generate_random_number
from ..db.user import User, UserSub
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

        # Set of shard ids this remote client is subscribed too
        self.shards = set()

    def modify_shard_subscription(self, shard, state):
        try:
            shard = Shard.get(Shard.id == shard).get().id

            # Grab or create the subscription (kind of weird we create on unsub...)
            sub, created = UserSub.get_or_create(
                user=self.user,
                shard=shard)
            sub.active = state
            sub.save()
        except Shard.DoesNotExist:
            pass

        if state:
            self.shards.add(shard)
        elif shard in self.shards:
            self.shards.remove(shard)

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
            elif isinstance(packet.inner, PacketOfferBlock):
                return self.handle_offer_block(packet)
            elif isinstance(packet.inner, PacketOfferEntry):
                return self.handle_offer_Entry(packet)
            elif isinstance(packet.inner, PacketRequestBlocks):
                return self.handle_request_blocks(packet)
            elif isinstance(packet.inner, PacketListBlocks):
                return self.handle_list_blocks(packet)
            elif isinstance(packet.inner, PacketRequestEntries):
                return self.handle_request_entries(packet)
            elif isinstance(packet.inner, PacketListEntries):
                return self.handle_list_entries(packet)


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

        for shard in packet.shards:
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
        self.send(PacketRequestPeers(maxsize=128, shards=self.parent.shards.keys()))

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
                print(shard)
                Shard.from_proto(shard)

        map(self.parent.add_peer, map(lambda i: '{}:{}'.format(i.ip, i.port), packet.peers))

    def handle_subscribe_shard(self, packet):
        self.modify_shard_subscription(shard.id, packet.state)

    def handle_offer_block(self, packet):
        try:
            shard = Shard.get(Shard.id == packet.shard)
        except Shard.DoesNotExist:
            log.info("Ignoring block offer for shard we don't know")
            return

        # Load the block
        block = Block.from_proto(packet.block)

        # If this block is already commited, skip it
        if block.commited:
            raise TrustException("Recieved offer for block we've already commited {}".format(block.id),
                TrustException.Level.INACCURATE)

        chain = self.parent.shards[shard.id].chain
        last = shard.get_last_block()

        # Validate the block
        try:
            chain.validate_block(last, block)
        except ChainValidationError:
            log.exception("Failed to consider block offer:")

        # Now commit it!
        block.commited = True
        block.save()

        # Start mining the next block
        if chain.worker:
            chain.worker.cancel()
            threading.Thread(target=self.chain.mine, args=(self.client.user, ))

        # TODO: detect a chain split here and make a decision
        # TODO: re-share this block to our peers

    def handle_offer_entry(self, packet):
        shard = self.parent.shards.get(packet.shard)
        if not shard:
            log.info("Ignoring entry offer for shard we don't know")
            return

        # Create the entry from the packet
        entry = Entry.from_proto(packet.entry)

        # TODO: TrustError
        if not entry.validate_proof():
            log.error("Recieved packet with invalid proof!")
            return

        if not shard.chain.worker:
            shard.chain.start_miner(self.parent.user)

    def handle_request_blocks(self, packet):
        try:
            shard = Shard.get(Shard.id == packet.shard)
        except Shard.DoesNotExist:
            log.warning("Ignoring request for blocks in a shard we don't have")
            return

        blocks = []

        if packet.start_id and packet.stop_id:
            try:
                start = Block.get(
                    (Block.id == packet.start) &
                    (Block.shard_id == shard.id))
            except Shard.DoesNotExist:
                log.error("Invalid block ID range")
                return

            # start + the rest of the packets
            blocks += list(Block.select().where(
                (Block.commited == True) &
                (Block.position >= start.position) &
                (Block.shard_id == shard.id)).order_by(Block.position).limit(32))

        if packet.start_index and packet.stop_index:
            if abs(packet.stop_index - packet.start_index) > 32:
                log.error("Block range is too large")
                return

            if packet.stop_index > 0 and packet.start_index > 0:
                r = range(packet.start_index, packet.stop_index + 1)
            elif packet.stop_index < 0 and packet.start_index < 0:
                r = range(packet.stop_index, packet.start_index - 1)
            else:
                log.error("Block range is invalid")
                return

            for dex in r:
                blocks.append(shard.get_block_at(dex))

        if packet.blocks:
            blocks += list(Block.select().where((Block.id << tuple(packet.blocks))))

        # Send response
        resp = PacketListBlocks()
        resp.blocks.extend([obj.to_proto(with_entries=not packet.brief) for obj in blocks])
        packet.respond(resp)

    def handle_list_blocks(self, packet):
        log.debug("got list blocks: {}".format(len(packet.blocks)))

    def handle_request_entries(self, packet):
        pass

    def handle_list_entries(self, packet):
        pass

