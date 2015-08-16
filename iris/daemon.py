import os, logging, shutil, json, sys, socket, threading, binascii, time

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

from .api.rest import RestProvider

log = logging.getLogger(__name__)

class DaemonException(Exception):
    pass

class IrisDaemon(object):
    def __init__(self, path, seeds=None, fork=True, **kwargs):
        self.path = os.path.expanduser(path)
        self.seeds = seeds
        self.fork = fork

        self.socket_path = os.path.join(self.path, 'daemon.sock')
        self.pidfile = os.path.join(self.path, 'pid')
        self.pid = None

        self.start_time = time.time()

        if not os.path.exists(self.path):
            raise DaemonException("Path `{}` does not exist".format(self.path))

        init_db(os.path.join(self.path, 'database.db'))
        self.load_profile()

        self.config = Config(os.path.join(self.path, 'config.json'))

        if kwargs.get('port'):
            self.config.local.port = kwargs['port']

        if self.seeds:
            self.seeds = list(filter(bool, self.seeds.split(',')))
        else:
            self.seeds = list(map(lambda i: '{}:{}'.format(i.ip, i.port), list(Seed.select())))

        if not len(self.seeds):
            raise DaemonException("Cannot run, we have no seeds!")

        self.shards = list(Shard.select())
        self.client = LocalClient(self.user, self.shards, config=self.config, seeds=self.seeds)
        self.rest_provider = RestProvider(self)

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
        self.user.secret_key = binascii.unhexlify(self.profile['secret_key'])

    def run(self):
        if self.fork:
            if os.path.exists(self.pidfile):
                raise DaemonException("Pid file exists, is another daemon process running?")

            self.pid = os.fork()
            if self.pid > 0:
                sys.exit(0)

            with open(self.pidfile, 'w') as f:
                f.write(str(self.pid))

        threading.Thread(target=self.rest_provider.run).start()
        self.client.run()

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
        user.nickname = input("Nickname? ")
        user.id = user.hash
        user.save(force_insert=True)
        user.verify_signature()

        with open(os.path.join(path, 'profile.json'), 'w') as f:
            base = user.to_dict()
            base['secret_key'] = binascii.hexlify(ident.secret_key).decode('utf-8')
            del base['signature']
            f.write(IrisJSONEncoder().encode(base))

        Config.create_config(os.path.join(path, 'config.json'))

        print("Created new profile at {}".format(path))

    @classmethod
    def create_entry(cls, args, path):
        init_db(os.path.join(path, 'database.db'))

        with open(os.path.join(path, 'profile.json')) as f:
            profile = json.load(f)

        user = User.get(User.id == profile['id'])
        user.secret_key = binascii.unhexlify(profile['secret_key'])

        with open(args['post'], 'r') as f:
            entry = Entry.create_from_json(user, json.load(f))

        print("Created new entry %s" % entry.id)

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
