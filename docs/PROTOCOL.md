# Iris Protocol
Iris is a distributed sharing protocol built on similar technology to bitcoin and bittorrent. It was designed to be a base for other applications and services to build from. Generally Iris can be seen as a broker for information, internally it handles extensive logic to aid in syncing, validating, and distributing data.

## Core Entities

### Shards
Shards are the base entities in Iris. They allow "scoping" data within a set number of peers, allowing segmentation and categorization of data.

### Entry
An entry is a post that is bound to a shard, and stored within a block. Entries are created by users and can generally contain arbitrary data (with some restricitions)

## Core Concepts

### Block Chain
Iris uses a block chain to verify historical validity and existance for its entries. Unlike bitcoin, Iris provides no explicit reward for mining (although it benefits users wanting to post).




