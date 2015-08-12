import os, logging, shutil, json, sys, socket, thread

from signal import SIGTERM

from .client.local import LocalClient
from .common.config import Config
from .common.identity import Identity
from .db.base import create_db, init_db
from .db.user import User
from .db.shard import Shard
from .db.entry import Entry
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
            res, suc = getattr(self, 'handle_{}'.format(data['action']))(data)
            res['success'] = suc
            return json.dumps(res)
        

        return json.dumps({
            "error": "Invalid action",
            "success": False
        })

class IrisDaemon(object):
    def __init__(self, path, seeds=None, fork=True, **kwargs):
        self.path = os.path.expanduser(path)
        self.seeds = seeds
        self.fork = fork

        self.socket_path = os.path.join(self.path, 'daemon.sock')
        self.pidfile = os.path.join(self.path, 'pid')
        self.pid = None

        if not os.path.exists(self.path):
            raise DaemonException("Path `{}` does not exist".format(self.path))

        init_db(os.path.join(self.path, 'database.db'))
        self.load_profile()

        self.config = Config(os.path.join(self.path, 'config.json'))

        if kwargs.get('port'):
            self.config.local.port = kwargs['port']

        if self.seeds:
            self.seeds = filter(bool, self.seeds).split(',')
        else:
            self.seeds = map(lambda i: '{}:{}'.format(i.ip, i.port), list(Seed.select()))

        if not len(self.seeds):
            raise DaemonException("Cannot run, we have no seeds!")

        self.shards = list(Shard.select())
        self.client = LocalClient(self.user, self.shards, config=self.config, seeds=self.seeds)

        try:
            self.run()
        except:
            raise
        finally:
            # print open(self.pidfile, 'r').read().strip(), self.pid
            if os.path.exists(self.pidfile) and str(self.pid) == open(self.pidfile, 'r').read().strip():
                os.remove(self.pidfile)

    def load_profile(self):
        with open(os.path.join(self.path, 'profile.json')) as f:
            self.profile = json.load(f)

        self.user = User.get(User.id == self.profile['id'])
        self.user.secret_key = self.profile['secret_key'].decode('hex')

    def run(self):
        if self.fork:
            if os.path.exists(self.pidfile):
                raise DaemonException("Pid file exists, is another daemon process running?")

            self.pid = os.fork()
            if self.pid > 0:
                sys.exit(0)

            with open(self.pidfile, 'w') as f:
                f.write(str(self.pid))
       
        self.client.run()
        self.rpc_server = IrisSocketRPCServer(self)
        self.rpc_server.serve()
        
    @classmethod
    def create_profile(cls, args, path):
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
        user.from_identity(ident)
        user.nickname = raw_input("Nickname? ")
        user.id = user.hash
        user.save(force_insert=True)
        
        with open(os.path.join(path, 'profile.json'), 'w') as f:
            base = user.to_dict()
            base['secret_key'] = ident.secret_key.encode('hex')
            del base['signature']
            f.write(IrisJSONEncoder().encode(base))

        Config.create_config(os.path.join(path, 'config.json'))

        print "Created new profile at {}".format(path)

    @classmethod
    def create_shard(cls, args, path):
        init_db(os.path.join(path, 'database.db'))

        shard = Shard()
        shard.name = raw_input("Name? ")
        shard.desc = raw_input("Desc? ")
        shard.public = raw_input("Public (Y/n)? ").lower()[0] == 'y'
        shard.meta = ""
        shard.id = shard.hash
        shard.save(force_insert=True)

        print "Created new shard %s" % shard.id
   
    @classmethod
    def create_entry(cls, args, path):
        init_db(os.path.join(path, 'database.db'))

        with open(os.path.join(path, 'profile.json')) as f:
            profile = json.load(f)

        user = User.get(User.id == profile['id'])
        user.secret_key = profile['secret_key'].decode('hex')

        with open(args['post'], 'r') as f:
            entry = Entry.create_from_json(user, json.load(f))

        print "Created new entry %s" % entry.id

    @classmethod
    def create_cli(cls, args):
        path = os.path.expanduser(args['path'])

        if args['type'] == 'profile':
            return cls.create_profile(args, path)
        elif args['type'] == 'shard':
            return cls.create_shard(args, path)
        elif args['type'] == 'entry':
            return cls.create_entry(args, path)

    @classmethod
    def from_cli(cls, args):
        nargs = {k: v for k, v in args.items() if k not in ['path', 'seed']}
        return cls(args['path'], args['seed'], not args['no_fork'], **nargs)
