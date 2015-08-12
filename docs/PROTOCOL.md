# Iris Protocol
Iris is a distributed sharing protocol that allows members to easily share arbitrarily structured data. It was designed to be a base for other applications and services to build from.

## Basic Concepts

### Authority
Iris does not have a central, or even elected authority. It is meant to be completely anonymous, distributed, and deterministic. It's security comes from having a wide and unopinionated network, similarly to most anonymous/distributed systems, it breaks down when one set of authority controls too much of the network (although it still gives some guarentees which makes it safer than other alternatives)

### Transport Layer
Iris is completely transport-layer agnostic. Although the Python proof of concept and similar libraries require session/stateful like transport layers, in theory Iris could work over any transport (HTTP, RPC, etc).

### Consistency
Iris provides _no_ guarentees about data consistency. This was a mindful choice allowing it to remain completely distributed, and hard to break. Through nifty features of the protocol, this data-inconsistency can be used to determine and isolate bad actors.

### Spam/Abuse
Iris implements a proof of work requirement for all actions and entries, making it hard to abuse.
