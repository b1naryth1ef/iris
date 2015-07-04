import time, thread, logging

from data.base_pb2 import *
from client.identity import Identity
from common.util import packet_from_id, packet_to_id, generate_random_number

log = logging.getLogger(__name__)

class RemoteClient(object):
    def __init__(self, parent, socket):
        self.parent = parent
        self.socket = socket

        self.identity = None
        self.auth_completed = False
        self.auth_challenge = None

    def send_handshake(self):
        packet = PacketBeginHandshake()
        packet.id = self.parent.identity.id
        packet.pubkey = self.parent.identity.pk
        packet.timestamp = int(time.time())
        packet.challenge = self.auth_challenge = generate_random_number(8)
        self.send(packet)

    def wait_for_handshake(self, delay=5):
        def _f():
            time.sleep(delay)
            if not self.auth_completed or not self.identity:
                self.close("failed to authenticate in time")
        thread.start_new_thread(_f, ())

    def update(self):
        packet = self.recv()
        self.handle(packet)

    @property
    def fileno(self):
        return self.socket.fileno()

    def send(self, packet, encrypt=True):
        encrypt = encrypt and self.identity
        data = packet.SerializeToString()

        if encrypt:
            data = self.parent.identity.encrypt(data, self.identity)

        obj = Packet()
        obj.type = packet_to_id(packet)
        obj.data = data

        log.debug("Sending packet %s to remote %s (%s)",
                packet.__class__.__name__, self.identity, 'encrypted' if encrypt else '')
        self.socket.send(obj.SerializeToString())

    def recv(self):
        data = self.socket.recv(4096)
        outer = Packet()
        outer.ParseFromString(data)

        if outer.type == 0:
            raise Exception("Invalid packet data read: `{}`".format(data))

        data = outer.data

        if self.identity and self.auth_completed:
            data = self.parent.identity.decrypt(data, self.identity)

        packet = packet_from_id(outer.type)()
        packet.ParseFromString(data)
        return packet

    def close(self, reason=None):
        log.warning("Disconnecting remote client %s (%s)", self.identity, reason or 'no reason')
        if reason:
            obj = PacketClose()
            obj.reason = reason
            self.send(obj)
        self.socket.close()

    def handle(self, packet):
        log.debug("Recieved packet %s", packet.__class__.__name__)
        if isinstance(packet, PacketBeginHandshake):
            self.handle_begin_handshake(packet)
        elif isinstance(packet, PacketDenyHandshake):
            self.handle_deny_handshake(packet)
        elif isinstance(packet, PacketAcceptHandshake):
            self.handle_accept_handshake(packet)
        elif isinstance(packet, PacketCompleteHandshake):
            self.handle_complete_handshake(packet)
        else:
            log.warning("Failed to handle packet %s", packet.__class__.__name__)

    def handle_begin_handshake(self, packet):
        # We do not allow re-negoationing or a new handshake
        if self.identity:
            self.close("R001 invalid handshake packet")
            raise Exception("R001: remote client sent handshake packet after a handshake was completed")

        diff = (time.time() - packet.timestamp)
        if abs(diff) > 30:
            self.close("R002: timestamp is too skewed to complete handshake")
            raise Exception("R002: timestamp skew to great")

        # Store identity info
        self.identity = Identity(packet.id, packet.pubkey)

        # TODO: we need to pull from our local db here and validate we haven't blocked this user

        # Construct response
        resp = PacketAcceptHandshake()
        resp.id = self.parent.identity.id
        resp.pubkey = self.parent.identity.pk
        resp.response = self.parent.identity.encrypt(str(packet.challenge), self.identity)
        resp.challenge = self.auth_challenge = generate_random_number(9)
        self.send(resp, False)

    def handle_deny_handshake(self, packet):
        pass
        # TODO: this

    def handle_accept_handshake(self, packet):
        # If we are already authed, or didn't send this packet we're in trouble
        if not self.auth_challenge or self.identity:
            self.close("R001 invalid handshake packet")
            raise Exception("R001: unexpected PacketAcceptHandshake packet")

        self.identity = Identity(packet.id, packet.pubkey)
        decoded = self.parent.identity.decrypt(packet.response, self.identity)

        if decoded != str(self.auth_challenge):
            self.close("invalid challenge response")
            raise Exception("Invalid challenge response for handshake accept")

        self.auth_completed = True

        # Now lets complete the three-way-shake
        resp = PacketCompleteHandshake()
        resp.response = self.parent.identity.encrypt(str(packet.challenge), self.identity)
        self.send(resp, False)

    def handle_complete_handshake(self, packet):
        if not self.auth_challenge or not self.identity or self.auth_completed:
            self.close("R001 invalid handshake packet")
            raise Exception("R001: unexpected PacketCompleteHandshake packet")

        decoded = self.parent.identity.decrypt(packet.response, self.identity)
        if decoded != str(self.auth_challenge):
            self.close("invalid challenge response")
            raise Exception("Invalid challenge response for handshake completion")

        self.auth_completed = True
        log.info("Completed 3-way handshake with %s", self.identity)
