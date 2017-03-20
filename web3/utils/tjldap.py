from django.conf import settings

from ldap3 import Server, Connection


def get_uid(username):
    if settings.DEBUG:
        from ..apps.users.helpers import generate_debug_id  # necessary to prevent recursive import

        return generate_debug_id(username)

    connection = Connection(Server(settings.LDAP_SERVER))
    connection.bind()
    connection.search("ou=people,dc=csl,dc=tjhsst,dc=edu",
                      "(&(objectClass=posixAccount)(uid={}))".format(username), attributes=["uidNumber"])
    return int(connection.response[0]["attributes"]["uidNumber"])


def get_full_name(username):
    if settings.DEBUG:
        return None

    connection = Connection(Server(settings.LDAP_SERVER))
    connection.bind()
    connection.search("ou=students,ou=people,dc=csl,dc=tjhsst,dc=edu",
                      "(&(objectClass=posixAccount)(uid={}))".format(username), attributes=["cn"])
    if len(connection.response):
        resp = connection.response[0]["attributes"]["cn"]
        return resp[0] if isinstance(resp, (list, tuple)) else resp
    else:
        return None
