from iris.db.block import Block
from iris.db.entry import Entry


class EffortCalculator(object):
    """
    Calculates the effort required to mine a block based on the shard and current
    chain status.
    """

    def __init__(self, shard):
        self.shard = shard

    def calculate(self, obj):
        if isinstance(obj, Block):
            # The initial block always has an effort of 6
            if obj.initial:
                return 6
            
            # TODO: maybe we should write a calculation...
            return 12
        elif isinstance(obj, Entry):
            return 6
        raise Exception("Cannot calculate effort for {}".format(obj.__class__.__name__))
