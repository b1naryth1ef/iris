import socket, sys, os, json, pprint

class IrisRPCClient(object):
    def __init__(self, path):
        self.socket_path = os.path.expanduser(path)
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.connect(self.socket_path)

    def __getattr__(self, name):
        try:
            return object.__getattribute__(self, name)
        except:
            def _f(*args, **kwargs):
                base = {'action': name}
                base.update(kwargs)
                self.socket.send(json.dumps(base))
                pprint.pprint(json.loads(self.socket.recv(2048)))

            return _f

class IrisCLI(object):
    @classmethod
    def from_cli(cls, args):
        client = IrisRPCClient(os.path.join(args['path'], 'daemon.sock'))

        if args['add_shard']:
            client.add_shard(id=args['add_shard'])
        elif args['stop']:
            client.stop()


