import os, logging, shutil, json, sys, socket, thread

from signal import SIGTERM

from .client.local import LocalClient
from .common.identity import Identity
from .db.base import create_db, init_db
from .db.user import User
from .db.seed import Seed
from .db.shard import Shard
from .common.util import IrisJSONEncoder
from .common.log import *

log = logging.getLogger(__name__)

class DaemonException(Exception):
    pass

class BaseRPCServer(object):
    def handle_status(self, obj):
        return {
            "pid": self.daemon.pid,
            "state": self.daemon.state,
        }

    def handle_stop(self, obj):
        os.kill(self.daemon.pid, SIGTERM)
        

class IrisSocketRPCServer(BaseRPCServer):
    def __init__(self, daemon):
        self.daemon = daemon

        if os.path.exists(self.daemon.socket_path):
            os.unlink(self.daemon.socket_path)

        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(self.daemon.socket_path)
        self.socket.listen(1)
    
    def serve(self):
        while True:
            conn, addr = self.socket.accept()
            thread.start_new_thread(self.handle_connection, (conn, addr))

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
            return json.dumps(getattr(self, 'handle_{}'.format(data['action']))(data))
        

class IrisDaemon(object):
    def __init__(self, path, port=None, seeds=None):
        self.path = os.path.expanduser(path)
        self.port = port
        self.seeds = seeds
        self.socket_path = os.path.join(self.path, 'daemon.sock')
        self.pidfile = os.path.join(self.path, 'pid')
        self.pid = None

        if not os.path.exists(self.path):
            raise DaemonException("Path `{}` does not exist".format(self.path))

        init_db(os.path.join(self.path, 'database.db'))

        with open(os.path.join(self.path, 'profile.json')) as f:
            self.profile = json.load(f)

        self.user = User.get(User.id == self.profile['id'])
        self.user.secret_key = self.profile['secret_key'].decode('hex')

        if self.seeds:
            self.seeds = filter(bool, self.seeds).split(',')
        else:
            self.seeds = map(lambda i: '{}:{}'.format(i.ip, i.port), list(Seed.select()))

        if not len(self.seeds):
            raise DaemonException("Cannot run, we have no seeds!")

        self.shards = map(lambda i: i.id, list(Shard.select()))
        self.client = LocalClient(self.user, self.shards, self.port, seeds=self.seeds)
        self.client.run()

        try:
            self.run()
        except:
            raise
        finally:
            # print open(self.pidfile, 'r').read().strip(), self.pid
            if os.path.exists(self.pidfile) and str(self.pid) == open(self.pidfile, 'r').read().strip():
                os.remove(self.pidfile)

    def run(self):
        if os.path.exists(self.pidfile):
            raise DaemonException("Pid file exists, is another daemon process running?")

        self.pid = os.fork()
        if self.pid > 0:
            sys.exit(0)

        with open(self.pidfile, 'w') as f:
            f.write(str(self.pid))
       
        self.rpc_server = IrisSocketRPCServer(self)
        self.rpc_server.serve()

    @classmethod
    def create_cli(cls, args):
        path = os.path.expanduser(args['path'])
        if os.path.exists(path):
            if not args['overwrite']:
                raise DaemonException("Path `{}` already exists, cannot create".format(path))
            shutil.rmtree(path)

        log.info("Attempting to create new iris profile at %s", path)
        os.mkdir(path)

        log.info("Creating database")
        create_db(os.path.join(path, 'database.db'))

        log.info("Creating new identity")
        ident = Identity.create()

        log.info("Creating new user")
        user = User()
        user.public_key = ident.public_key
        user.nickname = args['nickname']
        user.id = user.hash
        user.save(force_insert=True)
        
        with open(os.path.join(path, 'profile.json'), 'w') as f:
            base = user.to_dict()
            base['secret_key'] = ident.secret_key.encode('hex')
            f.write(IrisJSONEncoder().encode(base))

        print "Created new profile at {}".format(path)

    @classmethod
    def from_cli(cls, args):
        return cls(args['path'], args['port'], args['seed'])
