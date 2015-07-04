# Protocol
The iris protocol is transport agnostic and uses protobufs. Messages can optionally be encrypted with the recievers public-key.

## Protocol Rules

### R001 - Handshake Packet Ordering
Packets related to a connection handshake should never be transmitted after a connection has finished the two-way handshake, or in an unexpected order.

### R002 - Handshake Timestamp Difference
The unix timestamp embedded within the handshake request should, when recieved by the remote end, not exceed a duration of 30s from the current time.
