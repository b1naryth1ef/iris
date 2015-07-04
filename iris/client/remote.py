import time, thread

from data.base_pb2 import *
from common.util import packet_from_id, packet_to_id, generate_random_number

class RemoteClient(object):
    def __init__(self, parent, socket):
        self.parent = parent
        self.socket = socket
        self.user = None

    def handshake(self):
        packet = PacketBeginHandshake()
        packet.id = 'TOOD lol'
        packet.pubkey = 'TODO lol'
        packet.timestamp = int(time.time())
        packet.challenge = generate_random_number(8)
        self.send(packet)

    def wait_for_handshake(self, delay=5):
        def _f():
            time.sleep(delay)
            if not self.user:
                self.close("failed to authenticate")
        thread.start_new_thread(_f, ())

    def update(self):
        packet = self.recv()

        if isinstance(packet, PacketClose):
            print "Remote end is closing our connection ({})".format(packet.reason or 'no reason')
            self.close()
        elif isinstance(packet, PacketBeginHandshake):
            print 'got handshake packet!'

    @property
    def fileno(self):
        return self.socket.fileno()

    def send(self, packet):
        print 'sending?'
        obj = Packet()
        obj.type = packet_to_id(packet)
        print obj.type
        obj.data = packet.SerializeToString()
        self.socket.send(obj.SerializeToString())

    def recv(self):
        data = self.socket.recv(4096)
        outer = Packet()
        outer.ParseFromString(data)
       
        if outer.type == 0:
            raise Exception("Invalid packet data read: `{}`".format(data))

        packet = packet_from_id(outer.type)()
        packet.ParseFromString(outer.data)
        
        print 'loaded packet %s' % packet.__class__.__name__

    def close(self, reason=None):
        print 'Disconnecting client: %s' % (reason or 'no reason')
        if reason:
            obj = PacketClose()
            obj.reason = reason
            self.send(obj)
        self.socket.close()

