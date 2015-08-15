from .provider import APIProvider

class SocketProvider(APIProvider):
    """
    A socket API provider
    """

class BaseRPCServer(object):
    def handle_status(self, obj):
        return {
            "pid": self.daemon.pid,
            "state": self.daemon.state,
        }, True

    def handle_stop(self, obj):
        if self.daemon.pid:
            os.kill(self.daemon.pid, SIGTERM), True
        else:
            sys.exit(0)

    def handle_add_shard(self, obj):
        if self.daemon.client.add_shard(obj['id']):
            return {}, True
        else:
            return {}, False

class IrisSocketRPCServer(BaseRPCServer):
    def __init__(self, daemon):
        self.daemon = daemon

        if os.path.exists(self.daemon.socket_path):
            os.remove(self.daemon.socket_path)

        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(self.daemon.socket_path)
        self.socket.listen(1)

    def serve(self):
        while True:
            conn, addr = self.socket.accept()
            threading.Thread(target=self.handle_connection, args=(conn, addr)).start()

    def handle_connection(self, conn, addr):
        while True:
            data = conn.recv(2048)

            if not data:
                return

            try:
                data = json.loads(data)
            except:
                log.error("Failed to load packet for SocketRPCServer: `%s`", data)
                continue

            conn.sendall(self.handle_packet(conn, data))

    def handle_packet(self, conn, data):
        if not 'action' in data:
            return json.dumps({
                "error": "invalid request, missing action key",
                "success": False
            })

        if hasattr(self, 'handle_{}'.format(data['action'])):
            res, suc = getattr(self, 'handle_{}'.format(data['action']))(data)
            res['success'] = suc
            return json.dumps(res)


        return json.dumps({
            "error": "Invalid action",
            "success": False
        })

