import socket, select

class ProtocolUpdateEvent(object):
    NEW = 1
    DATA = 2
    CLOSE = 3

    def __init__(self, socket, update_type, data=None):
        self.socket = socket
        self.type = update_type
        self.__dict__.update(data or {})

class Protocol(object):
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.epoll = select.epoll()
        self.epoll.register(self.socket.fileno(), select.EPOLLIN)

    def close(self):
        self.socket.close()

    def listen(self, options=None):
        options = options or {}
        self.socket.bind((options.get('host', '0.0.0.0'), int(options['port'])))
        self.socket.listen(1)
        self.socket.setblocking(0)

    def connect(self, connstr):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host, port = connstr.split(':')
        try:
            s.connect((host, int(port)))
            self.epoll.register(s.fileno(), select.EPOLLIN)
        except:
            return None
        return s

    def poll(self, timeout=None):
        while True:
            for fno, event in self.epoll.poll(timeout or -1):
                if fno == self.socket.fileno():
                    if event & select.EPOLLHUP:
                        raise StopIteration

                    conn, addr = self.socket.accept()
                    conn.setblocking(0)
                    self.epoll.register(conn.fileno(), select.EPOLLIN)
                    yield ProtocolUpdateEvent(conn, ProtocolUpdateEvent.NEW)
                else:
                    if event & select.EPOLLIN:
                        self.epoll.modify(fno, 0)
                        yield ProtocolUpdateEvent(fno, ProtocolUpdateEvent.DATA)

                    if event & select.EPOLLHUP:
                        self.epoll.unregister(fno)
                        yield ProtocolUpdateEvent(fno, ProtocolUpdateEvent.CLOSE)

