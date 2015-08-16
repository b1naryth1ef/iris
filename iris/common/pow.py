import hashlib, logging

from multiprocessing import Process, Queue, cpu_count

log = logging.getLogger(__name__)

def prover(id, base, match, start, end, response):
    """
    Subprocess that attempts to prove a hash
    """
    log.info('[pow #{}] from {} to {}'.format(id, start, end))
    for answer in range(start, end):
        result = hashlib.sha256(str(answer).encode() + base).hexdigest()

        if result.startswith(match):
            response.put((id, True, answer, result))

    response.put((id, False, None, None))

class ProofOfWork(object):
    def __init__(self, load=1, char='0', cores=cpu_count(), inc=10000):
        self.load = load
        self.char = char
        self.cores = cores
        self.procs = {}
        self.id_inc = 0
        self.inc = inc
        self.current = 0
        self.q = Queue()

    def validate(self, base, answer):
        return hashlib.sha256(str(answer) + base).hexdigest().startswith(self.char * self.load)

    def add_process(self, base):
        self.id_inc += 1
        self.procs[self.id_inc] = Process(target=prover, args=(
            self.id_inc, base, self.char * self.load, self.current, self.current + self.inc, self.q
        ))
        self.current += self.inc
        self.procs[self.id_inc].start()

    def work(self, base, limit=None, inc=10000):
        if not isinstance(base, bytes):
            base = base.encode('utf8')
        
        # Seed the workers
        list(map(lambda i: self.add_process(base), range(self.cores)))
        
        while True:
            id, done, answer, result = self.q.get()
            
            self.procs[id].join()
            del self.procs[id]
            
            if done:
                for v in self.procs.values():
                    v.join()
                return answer, result
            
            self.add_process(base)

    def work2(self, base, limit=None):
        if not isinstance(base, bytes):
            base = base.encode('utf8')

        self.answer = 0
        current = hashlib.sha256(base).hexdigest()

        log.info("Attempting to prove work for hash {}, load {}".format(base, self.load))

        while not current.startswith(self.char * self.load):
            self.answer += 1
            current = hashlib.sha256(str.encode(str(self.answer)) + base).hexdigest()

            if limit and self.answer >= limit:
                log.warning("Failed to prove work before limit was reached")
                return

            if (self.answer % 10000) == 0:
                log.debug('  pow: {}'.format(self.answer))

        log.info("Proved work in {} rounds".format(self.answer))
        return self.answer, current

