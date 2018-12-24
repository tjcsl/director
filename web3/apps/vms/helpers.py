import json
import threading

import libvirt
import requests
from django.conf import settings
from raven.contrib.django.raven_compat.models import client


def call_api(action=None, **kwargs):
    try:
        if settings.CONDUCTOR_CERT_PATH:
            auth_args = {
                "cert": settings.CONDUCTOR_CERT_PATH,
                "verify": False
            }
        else:
            auth_args = {}

        resp = requests.request(method=("POST" if action else "GET"),
                                json={"method": action, "args": kwargs},
                                url=settings.CONDUCTOR_AGENT_PATH,
                                timeout=30,
                                **auth_args)
    except requests.exceptions.ConnectionError:
        client.captureException()
        return None
    except requests.exceptions.ReadTimeout:
        client.captureException()
        return None

    if resp.status_code == 500 or resp.status_code == 400:
        client.captureMessage(
            "Conductor API Request Failure: {} {}\n{} {}\n".format(resp.status_code, resp.text, action, kwargs))
        return None
    return json.loads(resp.text)


# store the connections to the lxc servers
lxc_connection_container = threading.local()
lxc_connection_container.connections = {}


# Get this thread's lxc connection.  Might not be necessary, but better safe than sorry
def get_connection(hostname) -> libvirt.virConnect:
    if hostname not in lxc_connection_container.connections:
        conn = libvirt.open('lxc+ssh://root@{}/'.format(hostname))
        lxc_connection_container.connections[hostname] = conn
    conn = lxc_connection_container.connections[hostname]
    # TODO: figure out how to check if a connection is still open
    return conn
