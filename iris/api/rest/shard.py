from .controller import *

from ...db.shard import Shard
from ...db.user import User
from ...db.block import Block

class ShardController(Controller):
    BASE_PATH = "/shards"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bp.add_url_rule('', 'shards_list', self.route_shards_list)
        self.bp.add_url_rule('/create', 'shards_create', self.route_shards_create, methods=['POST'])
        self.bp.add_url_rule('/add', 'shards_add', self.route_shards_add, methods=['POST'])
        self.bp.add_url_rule('/<id>', 'shards_info', self.route_shards_info)
        self.bp.add_url_rule('/<id>', 'shards_delete', self.route_shards_delete, methods=['DELETE'])
        self.bp.add_url_rule('/<id>/edit', 'shards_edit', self.route_shards_edit)
        self.bp.add_url_rule('/<id>/post', 'shards_post', self.route_shards_post, methods=['POST'])

    def route_shards_list(self):
        shards = Shard.select()

        raise APIResponse({
            "shards": list(map(lambda i: i.to_dict(), shards))
        })

    @with_object(Shard)
    def route_shards_info(self, shard):
        raise APIResponse({"shard": shard.to_dict()})

    def route_shards_create(self):
        data = require(request.json, name=str, desc=str, public=bool, meta=dict)

        shard = Shard(
            name=data['name'],
            desc=data['desc'],
            public=data['public'],
            meta=json.dumps(data['meta']))

        # Create the initial block
        block = Block(
            parent=None,
            solver=self.daemon.client.user,
            position='0',
            initial=True,
            commited=True)

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
        self.daemon.client.add_shard(shard.id, timeout=45)
        self.daemon.client.sync_shard(shard)

        raise APIResponse({
            "id": shard.id
        })

    def route_shards_add(self):
        if not request.values.get('id'):
            raise APIError("Missing ID")

        shard = self.daemon.client.add_shard(request.values.get('id'), timeout=45)
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

    @with_object(Shard)
    def route_shards_post(self, shard):
    
        pass
