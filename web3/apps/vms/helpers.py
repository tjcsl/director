import requests
import json

from django.conf import settings

from raven.contrib.django.raven_compat.models import client


def call_api(action=None, **kwargs):
    try:
        resp = requests.request(method=("POST" if action else "GET"), json={"method": action, "args": kwargs}, url=settings.CONDUCTOR_AGENT_PATH, cert=settings.CONDUCTOR_CERT_PATH, verify=False)
    except requests.exceptions.ConnectionError:
        return None

    if resp.status_code == 500 or resp.status_code == 400:
        if settings.DEBUG:
            print("{} {}\n{} {}".format(resp.status_code, resp.text, action, kwargs))
        else:
            client.captureMessage("Conductor API Request Failure: {} {}\n{} {}\n".format(resp.status_code, resp.text, action, kwargs))
        return None
    return json.loads(resp.text)
