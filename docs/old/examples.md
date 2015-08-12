## Publishing a Post to a feed

1. Create post content which looks like:
```
{
  # Random UUID
  "id": "60c8ba3d-13bb-44bd-8b3a-f8233e8dae53",

  # Generally the author data is just used for clients, but the ID must match the keypair ID
  "author": {
    "id": "e8e9f561-623f-44c0-a6cd-96a90da1a97a",
    "name": "joe55"
  },

  # Content can technically be any blob of text that fits within the feeds max-size
  "content": {
    "title": "Test Post Plz Ignore",
    "body": "..."
  },

  # Meta data
  "meta": {
    "blobs": {
      "pr0n.mp4": {}
    }
  }
}
```

2. Create network message:
```
hash: sha256(payload)
payload: payload
blobs:
  sha256(blob)
  blob
```

3. Ask the cluster to persist the message
  - We need to validate that each member persists the message, so we need an anonymous way to get the messages each node has
  - No send guarentee
4. Every 10 minutes there is a 15 second dark period where nodes compute a logical order to all the messages and attempt to reach quorum
  - What happens with divergance?
  - Look more into how BC handles this
5. The rollup is now part of the chain and references all the messages for this segment

Sample rollup:
```
id: uuid
payloads:
  payload_hashs
```
