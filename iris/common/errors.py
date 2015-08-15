
class TrustException(Exception):
    class Level(Exception):
        MALICIOUS = 1
        BROKEN = 2
        INACCURATE = 3
        UNKNOWN = 4
        NORMAL = 5
        ACCURATE = 6
        SAFE = 7
        GOD = 8

    def __init__(self, msg, trust):
        self.trust = trust
        Exception.__init__(self, msg)


