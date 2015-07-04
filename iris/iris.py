#!/usr/bin/env python
import sys, os, argparse

parser = argparse.ArgumentParser()
parser.add_argument('port', metavar='PORT')
parser.add_argument('seeds', metavar='SEEDS', nargs='+')
args = vars(parser.parse_args())

def main():
    from client.local import LocalClient
    c = LocalClient(args['port'], seeds=args['seeds'])

    try:
        c.run()
    except KeyboardInterrupt:
        c.stop()
    return 0

if __name__ == "__main__":
    sys.exit(main())

