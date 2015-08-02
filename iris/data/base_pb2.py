# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: base.proto

from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)




DESCRIPTOR = _descriptor.FileDescriptor(
  name='base.proto',
  package='',
  serialized_pb='\n\nbase.proto\"8\n\x04Peer\x12\x0e\n\x06pubkey\x18\x01 \x02(\t\x12\x0c\n\x04\x63onn\x18\x02 \x02(\t\x12\x12\n\nfirst_seen\x18\x03 \x02(\r\"1\n\x06Packet\x12\x19\n\x04type\x18\x01 \x02(\x0e\x32\x0b.PacketType\x12\x0c\n\x04\x64\x61ta\x18\x02 \x02(\x0c\"^\n\x14PacketBeginHandshake\x12\x0e\n\x06pubkey\x18\x01 \x02(\t\x12\x10\n\x08nickname\x18\x02 \x02(\t\x12\x11\n\ttimestamp\x18\x03 \x02(\r\x12\x11\n\tchallenge\x18\x04 \x02(\r\"6\n\x13PacketDenyHandshake\x12\x0e\n\x06reason\x18\x01 \x02(\t\x12\x0f\n\x07\x62\x61\x63koff\x18\x02 \x02(\r\"^\n\x15PacketAcceptHandshake\x12\x0e\n\x06pubkey\x18\x01 \x02(\t\x12\x10\n\x08nickname\x18\x02 \x02(\t\x12\x10\n\x08response\x18\x03 \x02(\x0c\x12\x11\n\tchallenge\x18\x04 \x02(\r\"+\n\x17PacketCompleteHandshake\x12\x10\n\x08response\x18\x01 \x02(\x0c\"2\n\nPacketPing\x12\x11\n\ttimestamp\x18\x01 \x02(\r\x12\x11\n\tchallenge\x18\x02 \x02(\r\"1\n\nPacketPong\x12\x11\n\ttimestamp\x18\x01 \x02(\r\x12\x10\n\x08response\x18\x02 \x02(\x0c\"\x1d\n\x0bPacketClose\x12\x0e\n\x06reason\x18\x01 \x01(\t\"5\n\x12PacketRequestPeers\x12\x0f\n\x07maxsize\x18\x01 \x02(\r\x12\x0e\n\x06shards\x18\x02 \x03(\t\"\'\n\x0fPacketListPeers\x12\x14\n\x05peers\x18\x01 \x03(\x0b\x32\x05.Peer*\xac\x01\n\nPacketType\x12\x0b\n\x07Invalid\x10\x00\x12\x12\n\x0e\x42\x65ginHandshake\x10\x01\x12\x11\n\rDenyHandshake\x10\x02\x12\x13\n\x0f\x41\x63\x63\x65ptHandshake\x10\x03\x12\x15\n\x11\x43ompleteHandshake\x10\x04\x12\x08\n\x04Ping\x10\x05\x12\x08\n\x04Pong\x10\x06\x12\t\n\x05\x43lose\x10\x07\x12\x10\n\x0cRequestPeers\x10\x08\x12\r\n\tListPeers\x10\t')

_PACKETTYPE = _descriptor.EnumDescriptor(
  name='PacketType',
  full_name='PacketType',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='Invalid', index=0, number=0,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='BeginHandshake', index=1, number=1,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='DenyHandshake', index=2, number=2,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='AcceptHandshake', index=3, number=3,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='CompleteHandshake', index=4, number=4,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='Ping', index=5, number=5,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='Pong', index=6, number=6,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='Close', index=7, number=7,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='RequestPeers', index=8, number=8,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ListPeers', index=9, number=9,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=647,
  serialized_end=819,
)

PacketType = enum_type_wrapper.EnumTypeWrapper(_PACKETTYPE)
Invalid = 0
BeginHandshake = 1
DenyHandshake = 2
AcceptHandshake = 3
CompleteHandshake = 4
Ping = 5
Pong = 6
Close = 7
RequestPeers = 8
ListPeers = 9



_PEER = _descriptor.Descriptor(
  name='Peer',
  full_name='Peer',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='pubkey', full_name='Peer.pubkey', index=0,
      number=1, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=unicode("", "utf-8"),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='conn', full_name='Peer.conn', index=1,
      number=2, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=unicode("", "utf-8"),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='first_seen', full_name='Peer.first_seen', index=2,
      number=3, type=13, cpp_type=3, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=14,
  serialized_end=70,
)


_PACKET = _descriptor.Descriptor(
  name='Packet',
  full_name='Packet',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='type', full_name='Packet.type', index=0,
      number=1, type=14, cpp_type=8, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='data', full_name='Packet.data', index=1,
      number=2, type=12, cpp_type=9, label=2,
      has_default_value=False, default_value="",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=72,
  serialized_end=121,
)


_PACKETBEGINHANDSHAKE = _descriptor.Descriptor(
  name='PacketBeginHandshake',
  full_name='PacketBeginHandshake',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='pubkey', full_name='PacketBeginHandshake.pubkey', index=0,
      number=1, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=unicode("", "utf-8"),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='nickname', full_name='PacketBeginHandshake.nickname', index=1,
      number=2, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=unicode("", "utf-8"),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='timestamp', full_name='PacketBeginHandshake.timestamp', index=2,
      number=3, type=13, cpp_type=3, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='challenge', full_name='PacketBeginHandshake.challenge', index=3,
      number=4, type=13, cpp_type=3, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=123,
  serialized_end=217,
)


_PACKETDENYHANDSHAKE = _descriptor.Descriptor(
  name='PacketDenyHandshake',
  full_name='PacketDenyHandshake',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='reason', full_name='PacketDenyHandshake.reason', index=0,
      number=1, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=unicode("", "utf-8"),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='backoff', full_name='PacketDenyHandshake.backoff', index=1,
      number=2, type=13, cpp_type=3, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=219,
  serialized_end=273,
)


_PACKETACCEPTHANDSHAKE = _descriptor.Descriptor(
  name='PacketAcceptHandshake',
  full_name='PacketAcceptHandshake',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='pubkey', full_name='PacketAcceptHandshake.pubkey', index=0,
      number=1, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=unicode("", "utf-8"),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='nickname', full_name='PacketAcceptHandshake.nickname', index=1,
      number=2, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=unicode("", "utf-8"),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='response', full_name='PacketAcceptHandshake.response', index=2,
      number=3, type=12, cpp_type=9, label=2,
      has_default_value=False, default_value="",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='challenge', full_name='PacketAcceptHandshake.challenge', index=3,
      number=4, type=13, cpp_type=3, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=275,
  serialized_end=369,
)


_PACKETCOMPLETEHANDSHAKE = _descriptor.Descriptor(
  name='PacketCompleteHandshake',
  full_name='PacketCompleteHandshake',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='response', full_name='PacketCompleteHandshake.response', index=0,
      number=1, type=12, cpp_type=9, label=2,
      has_default_value=False, default_value="",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=371,
  serialized_end=414,
)


_PACKETPING = _descriptor.Descriptor(
  name='PacketPing',
  full_name='PacketPing',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='timestamp', full_name='PacketPing.timestamp', index=0,
      number=1, type=13, cpp_type=3, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='challenge', full_name='PacketPing.challenge', index=1,
      number=2, type=13, cpp_type=3, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=416,
  serialized_end=466,
)


_PACKETPONG = _descriptor.Descriptor(
  name='PacketPong',
  full_name='PacketPong',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='timestamp', full_name='PacketPong.timestamp', index=0,
      number=1, type=13, cpp_type=3, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='response', full_name='PacketPong.response', index=1,
      number=2, type=12, cpp_type=9, label=2,
      has_default_value=False, default_value="",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=468,
  serialized_end=517,
)


_PACKETCLOSE = _descriptor.Descriptor(
  name='PacketClose',
  full_name='PacketClose',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='reason', full_name='PacketClose.reason', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=unicode("", "utf-8"),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=519,
  serialized_end=548,
)


_PACKETREQUESTPEERS = _descriptor.Descriptor(
  name='PacketRequestPeers',
  full_name='PacketRequestPeers',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='maxsize', full_name='PacketRequestPeers.maxsize', index=0,
      number=1, type=13, cpp_type=3, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='shards', full_name='PacketRequestPeers.shards', index=1,
      number=2, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=550,
  serialized_end=603,
)


_PACKETLISTPEERS = _descriptor.Descriptor(
  name='PacketListPeers',
  full_name='PacketListPeers',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='peers', full_name='PacketListPeers.peers', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=605,
  serialized_end=644,
)

_PACKET.fields_by_name['type'].enum_type = _PACKETTYPE
_PACKETLISTPEERS.fields_by_name['peers'].message_type = _PEER
DESCRIPTOR.message_types_by_name['Peer'] = _PEER
DESCRIPTOR.message_types_by_name['Packet'] = _PACKET
DESCRIPTOR.message_types_by_name['PacketBeginHandshake'] = _PACKETBEGINHANDSHAKE
DESCRIPTOR.message_types_by_name['PacketDenyHandshake'] = _PACKETDENYHANDSHAKE
DESCRIPTOR.message_types_by_name['PacketAcceptHandshake'] = _PACKETACCEPTHANDSHAKE
DESCRIPTOR.message_types_by_name['PacketCompleteHandshake'] = _PACKETCOMPLETEHANDSHAKE
DESCRIPTOR.message_types_by_name['PacketPing'] = _PACKETPING
DESCRIPTOR.message_types_by_name['PacketPong'] = _PACKETPONG
DESCRIPTOR.message_types_by_name['PacketClose'] = _PACKETCLOSE
DESCRIPTOR.message_types_by_name['PacketRequestPeers'] = _PACKETREQUESTPEERS
DESCRIPTOR.message_types_by_name['PacketListPeers'] = _PACKETLISTPEERS

class Peer(_message.Message):
  __metaclass__ = _reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _PEER

  # @@protoc_insertion_point(class_scope:Peer)

class Packet(_message.Message):
  __metaclass__ = _reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _PACKET

  # @@protoc_insertion_point(class_scope:Packet)

class PacketBeginHandshake(_message.Message):
  __metaclass__ = _reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _PACKETBEGINHANDSHAKE

  # @@protoc_insertion_point(class_scope:PacketBeginHandshake)

class PacketDenyHandshake(_message.Message):
  __metaclass__ = _reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _PACKETDENYHANDSHAKE

  # @@protoc_insertion_point(class_scope:PacketDenyHandshake)

class PacketAcceptHandshake(_message.Message):
  __metaclass__ = _reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _PACKETACCEPTHANDSHAKE

  # @@protoc_insertion_point(class_scope:PacketAcceptHandshake)

class PacketCompleteHandshake(_message.Message):
  __metaclass__ = _reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _PACKETCOMPLETEHANDSHAKE

  # @@protoc_insertion_point(class_scope:PacketCompleteHandshake)

class PacketPing(_message.Message):
  __metaclass__ = _reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _PACKETPING

  # @@protoc_insertion_point(class_scope:PacketPing)

class PacketPong(_message.Message):
  __metaclass__ = _reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _PACKETPONG

  # @@protoc_insertion_point(class_scope:PacketPong)

class PacketClose(_message.Message):
  __metaclass__ = _reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _PACKETCLOSE

  # @@protoc_insertion_point(class_scope:PacketClose)

class PacketRequestPeers(_message.Message):
  __metaclass__ = _reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _PACKETREQUESTPEERS

  # @@protoc_insertion_point(class_scope:PacketRequestPeers)

class PacketListPeers(_message.Message):
  __metaclass__ = _reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _PACKETLISTPEERS

  # @@protoc_insertion_point(class_scope:PacketListPeers)


# @@protoc_insertion_point(module_scope)
