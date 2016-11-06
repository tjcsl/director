from ldap3 import Server, Connection

def get_uid(username):
    connection = Connection(Server('ldap://openldap1.csl.tjhsst.edu'))
    connection.bind()

    connection.search("ou=students,ou=people,dc=csl,dc=tjhsst,dc=edu", "(&(objectClass=posixAccount)(uid={}))".format(username), attributes=["uidNumber"])
    if not len(connection.response):
        connection.search("ou=staff,ou=people,dc=csl,dc=tjhsst,dc=edu","(&(objectClass=posixAccount)(uid={}))".format(username), attributes=["uidNumber"])
    return int(connection.response[0]["attributes"]["uidNumber"][0])
