import time, thread, logging

from ..data.base_pb2 import *
from ..common.util import packet_from_id, packet_to_id, generate_random_number
from ..db.user import User

log = logging.getLogger(__name__)

class RemoteClient(object):
    def __init__(self, parent, socket):
        self.parent = parent
        self.socket = socket

        self.user = None
        self.auth_completed = False
        self.auth_challenge = None

    def wait_for_handshake(self, delay=5):
        def _f():
            time.sleep(delay)
            if not self.auth_completed or not self.user:
                self.close("failed to authenticate in time")
        thread.start_new_thread(_f, ())

    def update(self):
        packet = self.recv()
        self.handle(packet)

    @property
    def fileno(self):
        return self.socket.fileno()

    def send(self, packet, encrypt=True):
        encrypt = encrypt and self.user
        data = packet.SerializeToString()

        if encrypt:
            data = self.parent.user.encrypt(data, self.user)

        obj = Packet()
        obj.type = packet_to_id(packet)
        obj.data = data

        log.debug("Sending packet %s to remote %s (%s)",
                packet.__class__.__name__, self.user, 'encrypted' if encrypt else '')
        self.socket.send(obj.SerializeToString())

    def recv(self):
        data = self.socket.recv(4096)
        
        if not data:
            log.info("Lost connection to remote client %s", self.user)
            return self.close()

        outer = Packet()
        outer.ParseFromString(data)

        if outer.type == 0:
            raise Exception("Invalid packet data read: `{}`".format(data))

        data = outer.data

        if self.user and self.auth_completed:
            data = self.parent.user.decrypt(data, self.user)

        packet = packet_from_id(outer.type)()
        packet.ParseFromString(data)
        return packet

    def close(self, reason=None):
        log.warning("Disconnecting remote client %s (%s)", self.user, reason or 'no reason')
        if reason:
            obj = PacketClose()
            obj.reason = reason
            self.send(obj)
        self.socket.close()

    def handle(self, packet):
        log.debug("Recieved packet %s", packet.__class__.__name__)
        if isinstance(packet, PacketBeginHandshake):
            return self.handle_begin_handshake(packet)
        elif isinstance(packet, PacketDenyHandshake):
            return self.handle_deny_handshake(packet)
        elif isinstance(packet, PacketAcceptHandshake):
            return self.handle_accept_handshake(packet)
        elif isinstance(packet, PacketCompleteHandshake):
            return self.handle_complete_handshake(packet)

        if self.user and self.auth_completed:
            if isinstance(packet, PacketRequestPeers):
                return self.handle_request_peers(packet)

        log.warning("Failed to handle packet %s", packet.__class__.__name__)

    def handle_begin_handshake(self, packet):
        # We do not allow re-negoationing or a new handshake
        if self.user:
            self.close("R001 invalid handshake packet")
            raise Exception("R001: remote client sent handshake packet after a handshake was completed")

        diff = (time.time() - packet.timestamp)
        if abs(diff) > 30:
            self.close("R002: timestamp is too skewed to complete handshake")
            raise Exception("R002: timestamp skew to great")

        try:
            self.user = User.get(User.id == packet.pubkey)
        except User.DoesNotExist:
            log.info("Adding newly met user %s to DB", packet.pubkey)
            self.user = User.create(id=packet.pubkey, public_key=packet.pubkey.decode('hex'), nickname=packet.nickname)

        # Construct response
        resp = PacketAcceptHandshake()
        resp.pubkey = str(self.parent.user.public_key).encode('hex')
        resp.nickname = self.parent.user.nickname
        resp.response = self.parent.user.encrypt(str(packet.challenge), self.user)
        resp.challenge = self.auth_challenge = generate_random_number(9)
        self.send(resp, False)

    def handle_deny_handshake(self, packet):
        pass
        # TODO: this

    def handle_accept_handshake(self, packet):
        # If we are already authed, or didn't send this packet we're in trouble
        print self.auth_challenge, self.user
        if not self.auth_challenge or self.user:
            self.close("R001 invalid handshake packet")
            raise Exception("R001: unexpected PacketAcceptHandshake packet")

        try:
            self.user = User.get(User.id == packet.pubkey)
        except User.DoesNotExist:
            log.info("Adding newly met user %s to DB", packet.pubkey)
            self.user = User.create(id=packet.pubkey, public_key=packet.pubkey.decode('hex'), nickname=packet.nickname)
        
        decoded = self.parent.user.decrypt(packet.response, self.user)

        if decoded != str(self.auth_challenge):
            self.close("invalid challenge response")
            raise Exception("Invalid challenge response for handshake accept")

        self.auth_completed = True

        # Now lets complete the three-way-shake
        resp = PacketCompleteHandshake()
        resp.response = self.parent.user.encrypt(str(packet.challenge), self.user)
        self.send(resp, False)

        # Finally request a list of peers
        self.send(PacketRequestPeers(maxsize=128, shards=self.parent.shards))

    def handle_complete_handshake(self, packet):
        if not self.auth_challenge or not self.user or self.auth_completed:
            self.close("R001 invalid handshake packet")
            raise Exception("R001: unexpected PacketCompleteHandshake packet")

        decoded = self.parent.user.decrypt(packet.response, self.user)
        if decoded != str(self.auth_challenge):
            self.close("invalid challenge response")
            raise Exception("Invalid challenge response for handshake completion")

        self.auth_completed = True
        log.info("Completed 3-way handshake with %s", self.user)

    def handle_request_peers(self, packet):
        log.info("Would send %s peers", len(self.parent.clients) - 1)
        print packet.shards

        peers = map(lambda i: i.socket.getpeername(), self.parent.clients.values())
        peers = peers[:packet.maxsize]

        resp = PacketListPeers()


