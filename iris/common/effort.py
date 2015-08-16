
class EffortCalculator(object):
    """
    Calculates the effort required to mine a block based on the shard and current
    chain status.
    """

    def __init__(self, shard):
        self.shard = shard

    def calculate(self, block):
        # The initial block always has an effort of 6
        if block.initial:
            return 6
        
        # TODO: maybe we should write a calculation...
        return 12
