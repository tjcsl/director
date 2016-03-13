import json
import time
import logging
from flask import Flask, request, make_response, jsonify

method_registry = {}
logging.getLogger('werkzeug').setLevel(logging.ERROR)


class rpc:

    @staticmethod
    def method(method_name):
        def wrap(f):
            method_registry[method_name] = f
            return f
        return wrap

app = Flask(__name__)


@app.route('/', methods=['GET'])
def listmethods():
    return jsonify(methods=list(method_registry.keys()))


@app.route('/', methods=['POST'])
def dispatch():
    body = request.json
    method = body["method"]
    print("{} {}".format(int(time.time() * 1000), method))
    args = body["args"]
    tx = make_response(json.dumps(method_registry[method](**args)))
    tx.headers["Content-Type"] = "application/json"
    return tx

import agent.views.ping  # noqa
import agent.views.container  # noqa
import agent.views.hypervisor  # noqa
