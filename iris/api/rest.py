import time, json, functools
from flask import Flask, jsonify, request

from ..db.shard import Shard
from ..db.user import User
from ..db.block import Block

from ..common import __VERSION__
from .provider import APIProvider

class APIBase(Exception):
    pass

class APIResponse(APIBase):
    def __init__(self, data={}):
        self.data = data
        self.data['success'] = True

class APIError(APIBase):
    def __init__(self, msg, code=None):
        self.data = {
            'success': False,
            'msg': msg
        }

        if code:
            self.data['code'] = code

def with_object(obj):
    def deco(f):
        @functools.wraps(f)
        def _f(self, *args, **kwargs):
            try:
                a = obj.get(obj.id == kwargs['id'])
            except obj.DoesNotExist:
                raise APIError("Invalid {} ID".format(obj.__name__))
            del kwargs['id']
            return f(self, a, *args, **kwargs)
        return _f
    return deco

class RestProvider(APIProvider):
    """
    A REST API provider
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.app = Flask("iris-rest")

        # Make sure we have config
        if 'rest' not in self.daemon.config.providers:
            raise Exception("No config for RestProvider (need config.providers.rest)")

        self.config = self.daemon.config.providers['rest']

        # Grab config vars
        self.host = self.config.get("host", "0.0.0.0")
        self.port = self.config.get("port", "8080")
        self.auth = self.config.get("auth")

        # Meta Registers
        self.app.register_error_handler(APIBase, self.handle_response)
        self.app.before_request(self.before_request)

        # Shards
        self.app.add_url_rule('/', 'index', self.route_index)
        self.app.add_url_rule('/shards', 'shards_list', self.route_shards_list)
        self.app.add_url_rule('/shards/create', 'shards_create', self.route_shards_create, methods=['POST'])
        self.app.add_url_rule('/shards/add', 'shards_add', self.route_shards_add, methods=['POST'])
        self.app.add_url_rule('/shards/<id>', 'shards_info', self.route_shards_info)
        self.app.add_url_rule('/shards/<id>', 'shards_delete', self.route_shards_delete, methods=['DELETE'])
        self.app.add_url_rule('/shards/<id>/edit', 'shards_edit', self.route_shards_edit)
        self.app.add_url_rule('/shards/<id>/sync', 'shards_sync', self.route_shards_sync)

    def before_request(self):
        if self.auth and request.headers.get("IRIS_AUTH") != self.auth:
            raise APIError("Invalid Credentials", 1000)

    def handle_response(self, obj):
        return jsonify(obj.data)

    def run(self):
        super().run()
        self.app.run(host=self.host, port=self.port)

    def route_index(self):
        raise APIResponse({
            "stats": {
                "uptime": float("{0:.4f}".format(time.time() - self.daemon.start_time)),
            },
            "version": __VERSION__
        })

    def route_shards_list(self):
        shards = Shard.select()

        raise APIResponse({
            "shards": list(map(lambda i: i.to_dict(), shards))
        })

    @with_object(Shard)
    def route_shards_info(self, shard):
        raise APIResponse({"shard": shard.to_dict()})

    def route_shards_create(self):
        try:
            shard = Shard(
                name=request.json['name'],
                desc=request.json['desc'],
                public=request.json['public'],
                meta=json.dumps(request.json.get('meta', {})))
        except KeyError as e:
            raise APIError("Invalid Payload: {}".format(e))

        # Create the initial block
        block = Block(
            parent=None,
            solver=self.daemon.client.user,
            position='0',
            initial=True)

        # Solve the initial block and save it
        worker = shard.get_block_pow(block)
        block.proof, _ = worker.work(block.hash)
        block.id = block.hash
        block.save(force_insert=True)

        # Now finish creating the shard
        shard.initial = block
        shard.id = shard.hash
        shard.save(force_insert=True)

        # Finally, update our block with a utility reference to the shard
        block.shard_id = shard.id
        block.save()

        # Add the shard to the client
        self.daemon.client.add_shard(shard.id)

        raise APIResponse({
            "id": shard.id
        })

    def route_shards_add(self):
        if not request.values.get('id'):
            raise APIError("Missing ID")

        shard = self.daemon.client.add_shard(request.values.get('id'))
        raise APIResponse({})

    @with_object(Shard)
    def route_shards_delete(self, shard):
        shard.delete_instance()
        raise APIResponse({})

    @with_object(Shard)
    def route_shards_edit(self, shard):
        if 'active' in request.json:
            shard.active = request.json['active']

            if shard.active == False and shard.id in self.daemon.client.shards:
                del self.daemon.client.shards[shard.id]

        shard.save()
        raise APIResponse({})

    def route_shards_sync(self, id):
        pass

