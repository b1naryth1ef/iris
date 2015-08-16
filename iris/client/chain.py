import logging

from ..common.pow import ProofOfWork

log = logging.getLogger(__name__)

class ChainValidationError(Exception):
    pass

class Chain(object):
    """
    Represents the "virtual" object that is a block chain.
    """
    def __init__(self, shard):
        self.shard = shard
        self.worker = None

    def mine(self, user):
        """
        Attempts to mine the next block in the chain.
        """
        # Grab all entries that have not been commited to a chain yet
        entries = Entry.get_uncommited_entries()

        # Get the last block that was mined
        last_block = shard.get_last_block()

        # Create a new block
        block = Block(
            parent=last_block,
            solver=user,
            position=str(int(last_block.position) + 1),
            shard_id=shard.id)

        # Try to mine it, we'll cancel this if we fail
        self.worker = self.shard.get_block_pow(block)
        block.proof, _ = worker.work(block.hash, cores=round(worker.cores / 4) or 1)

        if not block.proof:
            log.debug("Failed to mine block, I seem to have gotten cancelled!")
            return

        # TODO: announce to the world how successful we are
        block.save()
        self.worker = None

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

