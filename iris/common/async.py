from threading import Thread, Lock

class FutureCancelled(Exception):
    pass

class Future(object):
    def __init__(self):
        self.subs = []
        
        self.woken = False
        self.completed = False
        self.cancelled = False
        self.value = None
        self.exe = None

    def add_sub(self):
        lock = Lock()
        lock.acquire()
        self.subs.append(lock)
        return lock

    def wake_children(self):
        if self.woken:
            return
        
        self.woken = True

        for sub in self.subs:
            sub.release()

    def done(self, value):
        self.completed = True
        self.value = value
        self.wake_children()

    def cancel(self, exe=None):
        self.exe = exe
        self.completed = True
        self.cancelled = True
        self.wake_children()

    def wait(self, timeout=-1, ignore_error=False):
        lock = self.add_sub()
        lock.acquire(timeout=timeout)

        if self.exe and not ignore_error:
            raise self.exe

        if not self.cancelled:
            return self.value

        raise FutureCancelled()

