from ldap3 import Server, Connection


def get_uid(username):
    connection = Connection(Server('ldap://openldap1.csl.tjhsst.edu'))
    connection.bind()
    connection.search("ou=people,dc=csl,dc=tjhsst,dc=edu",
                      "(&(objectClass=posixAccount)(uid={}))".format(username), attributes=["uidNumber"])
    return int(connection.response[0]["attributes"]["uidNumber"])


def get_full_name(username):
    connection = Connection(Server('ldap://openldap1.csl.tjhsst.edu'))
    connection.bind()
    connection.search("ou=students,ou=people,dc=csl,dc=tjhsst,dc=edu",
                      "(&(objectClass=posixAccount)(uid={}))".format(username), attributes=["cn"])
    if len(connection.response):
        resp = connection.response[0]["attributes"]["cn"]
        return resp[0] if isinstance(resp, (list, tuple)) else resp
    else:
        return None
