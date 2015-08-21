import json

from .controller import *

# from ...db.shard import Shard
# from ...db.user import User
# from ...db.block import Block
from iris.db.shard import Shard
from iris.db.entry import Entry

class EntryController(Controller):
    BASE_PATH = "/entries"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bp.add_url_rule('/create', 'entries_create', self.route_entries_create, methods=['POST'])
        self.bp.add_url_rule('/search', 'entries_search', self.route_entries_search)
        self.bp.add_url_rule('/entries/<id>', 'entries_info', self.route_entries_info)
        self.bp.add_url_rule('/entries/<id>/download', 'entries_download', self.route_entries_download)

    def route_entries_create(self):
        data = require(request.json, shard=str, meta=dict, payload=str)

        try:
            shard = Shard.get(Shard.id == data['shard'])
        except Shard.DoesNotExist:
            raise APIError("Unknown shard ID: {}".format(data['shard']))

        entry = Entry()
        entry.shard = shard
        entry.author = self.daemon.client.user
        entry.meta = json.dumps(data['meta'])
        entry.set_payload(data['payload'])
        entry.id = entry.hash

        # Now, lets prove our work
        worker = entry.shard.get_pow(entry)
        entry.proof, _ = worker.work(entry.hash)

        entry.save(force_insert=True)
        raise APIResponse({"id": entry.id})

    def route_entries_search(self):
        pass

    @with_object(Entry)
    def route_entries_info(self, entry):
        pass

    @with_object(Entry)
    def route_entries_download(self, entry):
        pass

