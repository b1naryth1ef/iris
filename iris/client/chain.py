from ..common.pow import ProofOfWork

class ChainValidationError(Exception):
    pass

class Chain(object):
    """
    Represents the "virtual" object that is a block chain.
    """
    def __init__(self, shard):
        self.shard = shard
        self.mining = False

    def mine(self):
        """
        Attempts to mine the next block in the chain.
        """
        self.mining = True

    def validate_chain(self, blocks):
        """
        Validates a portion of a blockchain. This function assumes the user
        inherently trusts the first block, regardless of whether it is the
        true origin of the chain or not.
        """

        # If this is the seed block, it may not have any entries
        if blocks[0].id == self.shard.initial:
            if len(blocks[0].entries) == 0:
                raise ChainValidationError("First block is invalid as it has entries")

        # Check all the blocks in our mini-chain for validity
        for idx, block in enumerate(blocks[1:]):
            self.validate_block(shard, blocks[idx - 1], block)

        return True

    def validate_block(self, parent, block):
        """
        Validates a single block in the chain. This function assumes that the
        parent block passed has already been validated, and is trusted.
        """
        worker = self.shard.get_block_pow(block)

        if block.parent != parent:
            raise ChainValidationError("Block `{}` does not have `{}` as a parent".format(
                block.id, parent.id))

            # Verify the signature (e.g. someone didn't steal or spoof this block)
            if not block.verify_signature():
                raise ChainValidationError("Block signature for `{}` is invalid".format(block.id))

            # Verify the proof of work (e.g. someone didn't fake this block)
            if not worker.validate(block.id, block.proof):
                raise ChainValidationError("Block proof for `{}` is invalid".format(block.id))

        return True

