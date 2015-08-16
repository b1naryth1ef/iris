
# Blocks
## Initial Blocks
Initial blocks are very quirky by nature due to the fact they don't follow the standard linear block-chain path. The following attributes are special about initial blocks:

- Initial blocks have no parent (e.g. a null value for their parent)
- Initial blocks have no entries

### Initial Block Duplication
Due to the shard-binding quirk, it is theoritically possible for two chains to share the same initial block. This is possible because:

1. Initial blocks have no parent in their hash
2. Initial blocks have no shard in their hash

Although this could result in a slightly awkward and confusing situation, it should have no negetive effect on the network as all entries for subsequent blocks must be bound to the preferred shard.

## Shard Binding
Due to the recursive dependency of Shards to Blocks, blocks are the only entity in iris that is not bound to shards. Instead, blockchains are intrinsically bound to shards by the fact all their entries will have the shard-binding requirement.

