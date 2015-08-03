#!/usr/bin/env python
import sys, os, argparse

from iris.daemon import IrisDaemon
from iris.cli import IrisCLI

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(help='sub-command help', dest='command')

# Create mode
create_parser = subparsers.add_parser('create', help='create new iris entites') 
create_parser.add_argument('type', default='profile')
create_parser.add_argument('--path', default='~/.iris')
create_parser.add_argument('--overwrite', action='store_true', help='overwrite if exists')
create_parser.add_argument('--post', default='', help='path to post for creation')

# Daemon Mode
daemon_parser = subparsers.add_parser('daemon', help='manage a iris client daemon process')
daemon_parser.add_argument('--path', default='~/.iris')
daemon_parser.add_argument('--port', default=9090, type=int, help='port for the iris client to run on')
daemon_parser.add_argument('--seed', required=False, help='a comma-seperated value of ip:port combinations to seed from')
daemon_parser.add_argument('--no-fork', action='store_true', help='do not fork when running the daemon')
daemon_parser.add_argument('--upnp', action='store_true', help='attempt to port forward using UPnP mapping')

# Client mode
client_parser = subparsers.add_parser('cli', help='manage a remote iris daemon')
client_parser.add_argument('--path', default='~/.iris')
client_parser.add_argument('--status', action='store_true')
client_parser.add_argument('--stop', action='store_true')
client_parser.add_argument('--add-shard', default=None, help='attempt to add a shard from the peers we have')

def main():
    args = vars(parser.parse_args())
    
    if args['command'] == 'create':
        IrisDaemon.create_cli(args)
    elif args['command'] == 'daemon':
        IrisDaemon.from_cli(args)
    elif args['command'] == 'cli':
        IrisCLI.from_cli(args)
    else:
        parser.print_help()
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())

