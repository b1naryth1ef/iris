import time, json, functools, logging
from flask import Flask, jsonify, request

from ...common import __VERSION__
from ..provider import APIProvider

from .controller import *
from .shard import ShardController
from .entry import EntryController

log = logging.getLogger(__name__)

class RestProvider(APIProvider):
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

        self.app.add_url_rule('/', 'index', self.route_index)

        # Controllers
        self.app.register_blueprint(ShardController(self).bp)
        self.app.register_blueprint(EntryController(self).bp)

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

