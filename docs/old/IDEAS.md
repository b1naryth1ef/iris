
## Simple Post Creation
1. Create a UUID and hash for post
2. Ask N peers to validate post, which consistents of them returning a signed version of the validation request. Each node requires a proof of work before posting.
3. Ask all peers to propagate the post, this requires another proof of work per-node.
4. Each peer will attempt to continue transmitting the post across the network. It will only send each message once.

## Notaries
Min: 10 (some nodes may require other values, generally you want to max this out)
Max: 2048

## Long term post storage
Iris will give no guarantees about how long a post will be kept within a network, each node will need to make decisions about what it stores locally. Generally nodes will store either N many bytes, or N many days of posts.

## Potential Attacks

### Ignoring Validation
If a peer ignores a validation request, it will immediatly be marked invalid locally and ignored from the network in the future

### Ignoring Propagation
Peers can neglect to "seed" a post, but must ALWAYS respond whether they have validated or seen the post. A node can validate whether a peer is trustworthy by checking the signed-payload for a message (e.g. I say I have never seen post 1, but I have signed and validated post 1)

### Spam
Peers cannot spam the network at a heavy rate due to proof of work requirements

### Split Brain / Bad Actors
In the case of a set number of bad actors, the network should naturally segment itself in a safe way (unless new peers only connect to bad peers in the network, in which case the network is already invalid). All nodes can validate the trustworthy of a node based on their willingness to share and validate data, and can share the trust level of any peer with anyone in the network.

```
{
  "payload": "my data here",
  "notaries": {id: signed(checksum) ...},
  "id": "uuid-here"
}
```
