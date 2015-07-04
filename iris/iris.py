#!/usr/bin/env python
import sys, os, argparse

parser = argparse.ArgumentParser()
parser.add_argument('id', metavar='ID')
parser.add_argument('port', metavar='PORT')
parser.add_argument('seeds', metavar='SEEDS', nargs='+')
args = vars(parser.parse_args())

def main():
    import common.log
    from client.local import LocalClient
    from client.identity import Identity

    path = '/tmp/{}.json'.format(args['id'])

    if not os.path.exists(path):
        print 'creating identity'
        i = Identity.create()
        i.save(path, True)
    else:
        i = Identity.load(path)

    c = LocalClient(i, args['port'], seeds=args['seeds'])
    try:
        c.run()
    except KeyboardInterrupt:
        c.stop()
    return 0

if __name__ == "__main__":
    sys.exit(main())

