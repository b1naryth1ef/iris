import hashlib, logging

log = logging.getLogger(__name__)

class ProofOfWork(object):
    def __init__(self, load=1, char='0'):
        self.load = load
        self.char = char 

    def validate(self, base, answer):
        return hashlib.sha256(answer + base).startswith(self.char * self.load)

    def work(self, base, limit=None):
        self.answer = 0
        current = hashlib.sha256(base).hexdigest()

        log.info("Attempting to prove work for hash %s, load %s", (base, self.load))

        while not current.startswith(self.char * self.load):
            self.answer += 1
            current = hashlib.sha256(str(self.answer) + base).hexdigest()
            
            if limit and self.answer >= limit:
                log.warning("Failed to prove work before limit was reached")
                return

        log.info("Proved work in %s rounds" % self.answer)
        return self.answer, current
